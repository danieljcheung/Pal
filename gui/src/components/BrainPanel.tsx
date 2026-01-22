import { useState, useEffect, useRef } from "react";
import { fetchBrain, fetchIdentity, type Brain, type Identity, type Topic } from "../api";
import "./BrainPanel.css";

interface BrainPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

type TabType = "overview" | "skills" | "knowledge" | "thoughts";

// Evolution stages based on level
const EVOLUTION_STAGES = [
  { name: "Newborn", minLevel: 1 },
  { name: "Curious", minLevel: 5 },
  { name: "Companion", minLevel: 15 },
  { name: "Trusted", minLevel: 30 },
];

// Skill definitions with tree structure
const SKILL_TREE: Record<string, {
  name: string;
  tier: number;
  requires: string[];
  description: string;
  unlockReq: string;
  getProgress: (stats: Brain["stats"], topics: Record<string, Topic>) => { current: number; target: number };
}> = {
  greet: {
    name: "Greeting",
    tier: 1,
    requires: [],
    description: "Warmly greet returning friends",
    unlockReq: "10 check-ins",
    getProgress: (stats) => ({ current: stats.check_ins || 0, target: 10 }),
  },
  concern: {
    name: "Empathy",
    tier: 1,
    requires: [],
    description: "Notice and respond to emotions",
    unlockReq: "10 emotional shares",
    getProgress: (stats) => ({ current: stats.emotional_shares || 0, target: 10 }),
  },
  recall: {
    name: "Recall",
    tier: 2,
    requires: ["greet"],
    description: "Actively recall memories",
    unlockReq: "25 memories",
    getProgress: (stats) => ({ current: stats.memories_stored || 0, target: 25 }),
  },
  time_sense: {
    name: "Time Sense",
    tier: 2,
    requires: ["greet"],
    description: "Awareness of time passing",
    unlockReq: "50 messages, 3 days",
    getProgress: (stats) => ({ current: stats.messages_exchanged || 0, target: 50 }),
  },
  research: {
    name: "Research",
    tier: 2,
    requires: ["concern"],
    description: "Ask follow-up questions",
    unlockReq: "3 topics with questions",
    getProgress: (_, topics) => ({
      current: Object.values(topics).filter(t => t.unresolved?.length > 0).length,
      target: 3,
    }),
  },
  remind: {
    name: "Remind",
    tier: 3,
    requires: ["recall"],
    description: "Remember to remind you",
    unlockReq: "5 reminder requests",
    getProgress: (stats) => ({ current: stats.reminders_requested || 0, target: 5 }),
  },
  hold_thoughts: {
    name: "Hold Thoughts",
    tier: 3,
    requires: ["recall", "concern"],
    description: "Keep thoughts for later",
    unlockReq: "20 thought dumps",
    getProgress: (stats) => ({ current: stats.thought_dumps || 0, target: 20 }),
  },
  notice_patterns: {
    name: "Patterns",
    tier: 3,
    requires: ["research"],
    description: "Notice patterns over time",
    unlockReq: "50 memories",
    getProgress: (stats) => ({ current: stats.memories_stored || 0, target: 50 }),
  },
  tasks: {
    name: "Tasks",
    tier: 4,
    requires: ["remind"],
    description: "Track tasks for you",
    unlockReq: "5 reminders delivered",
    getProgress: (stats) => ({ current: stats.reminders_delivered || 0, target: 5 }),
  },
  opinions: {
    name: "Opinions",
    tier: 4,
    requires: ["hold_thoughts", "notice_patterns"],
    description: "Form and share opinions",
    unlockReq: "100 messages",
    getProgress: (stats) => ({ current: stats.messages_exchanged || 0, target: 100 }),
  },
  summarize: {
    name: "Summarize",
    tier: 4,
    requires: ["notice_patterns"],
    description: "Summarize knowledge",
    unlockReq: "100 memories",
    getProgress: (stats) => ({ current: stats.memories_stored || 0, target: 100 }),
  },
};

// Calculate Pal's level from stats
function calculateLevel(stats: Brain["stats"] | undefined): { level: number; xp: number; xpToNext: number } {
  if (!stats) return { level: 1, xp: 0, xpToNext: 100 };

  const totalXP =
    (stats.messages_exchanged || 0) * 2 +
    (stats.memories_stored || 0) * 5 +
    (stats.check_ins || 0) * 10 +
    (stats.emotional_shares || 0) * 3 +
    (stats.unique_days?.length || 0) * 20;

  // Level thresholds: 100, 250, 500, 800, 1200, 1700, etc.
  let level = 1;
  let threshold = 100;
  let prevThreshold = 0;

  while (totalXP >= threshold) {
    level++;
    prevThreshold = threshold;
    threshold += 100 + level * 50;
  }

  const xpInLevel = totalXP - prevThreshold;
  const xpForLevel = threshold - prevThreshold;

  return {
    level,
    xp: xpInLevel,
    xpToNext: xpForLevel,
  };
}

// Get current evolution stage
function getEvolutionStage(level: number): { current: string; index: number } {
  let stageIndex = 0;
  for (let i = EVOLUTION_STAGES.length - 1; i >= 0; i--) {
    if (level >= EVOLUTION_STAGES[i].minLevel) {
      stageIndex = i;
      break;
    }
  }
  return { current: EVOLUTION_STAGES[stageIndex].name, index: stageIndex };
}

// Calculate bond and knowledge scores
function calculateStats(stats: Brain["stats"] | undefined, memoryCount: number, topicsCount: number) {
  if (!stats) return { bond: 0, knowledge: 0 };

  const bond = Math.min(100, Math.round(
    ((stats.check_ins || 0) * 3 +
    (stats.emotional_shares || 0) * 5 +
    (stats.unique_days?.length || 0) * 2)
  ));

  const knowledge = Math.min(100, Math.round(
    (memoryCount * 2 + topicsCount * 10)
  ));

  return { bond, knowledge };
}

// Understanding level to numeric
const UNDERSTANDING_VALUES: Record<string, number> = {
  surface: 1,
  basic: 2,
  familiar: 3,
  knowledgeable: 4,
};

function BrainPanel({ isOpen, onClose }: BrainPanelProps) {
  const [brain, setBrain] = useState<Brain | null>(null);
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("overview");
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  // Fetch data when panel opens
  useEffect(() => {
    if (!isOpen) return;

    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [brainData, identityData] = await Promise.all([
          fetchBrain(),
          fetchIdentity(),
        ]);
        setBrain(brainData);
        setIdentity(identityData);
      } catch {
        setError("Could not connect to Pal");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Reset tab when closing
  useEffect(() => {
    if (!isOpen) {
      setSelectedSkill(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const stats = brain?.stats;
  const skills = brain?.skills || {};
  const topics = brain?.topics || {};
  const innerLife = brain?.inner_life;

  const { level, xp, xpToNext } = calculateLevel(stats);
  const evolution = getEvolutionStage(level);
  const { bond, knowledge } = calculateStats(stats, brain?.memory_count || 0, Object.keys(topics).length);

  const pendingThoughts = innerLife?.thought_queue?.filter(t => !t.surfaced) || [];
  const recentDreams = innerLife?.dream_journal?.slice(-3) || [];
  const unresolvedCount = Object.values(topics).reduce((sum, t) => sum + (t.unresolved?.length || 0), 0);

  // Handle backdrop click
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // Render skill tree nodes
  const renderSkillTree = () => {
    const tiers = [1, 2, 3, 4];

    return (
      <div className="skill-tree">
        {tiers.map((tier) => {
          const tierSkills = Object.entries(SKILL_TREE).filter(([, s]) => s.tier === tier);
          return (
            <div key={tier} className="skill-tree__tier">
              {tierSkills.map(([id, skill]) => {
                const isUnlocked = skills[id]?.unlocked || false;
                const progress = skill.getProgress(stats || {} as Brain["stats"], topics);
                const progressPercent = Math.min(100, (progress.current / progress.target) * 100);
                const isClose = !isUnlocked && progressPercent >= 50;
                const isSelected = selectedSkill === id;

                // Check if requirements are met
                const reqsMet = skill.requires.every(req => skills[req]?.unlocked);

                return (
                  <div key={id} className="skill-node-wrapper">
                    {/* Connection lines to requirements */}
                    {skill.requires.map((req) => (
                      <div
                        key={req}
                        className={`skill-connection skill-connection--${req} ${skills[req]?.unlocked ? "skill-connection--active" : ""}`}
                      />
                    ))}

                    <button
                      className={`skill-node ${isUnlocked ? "skill-node--unlocked" : ""} ${isClose ? "skill-node--close" : ""} ${isSelected ? "skill-node--selected" : ""} ${!reqsMet && !isUnlocked ? "skill-node--unavailable" : ""}`}
                      onClick={() => setSelectedSkill(isSelected ? null : id)}
                    >
                      <span className="skill-node__name">{skill.name}</span>
                      {isUnlocked && <span className="skill-node__level">Lv.{skills[id]?.level || 1}</span>}
                    </button>

                    {/* Tooltip */}
                    {isSelected && (
                      <div className="skill-tooltip">
                        <div className="skill-tooltip__name">{skill.name}</div>
                        <div className="skill-tooltip__desc">{skill.description}</div>
                        <div className="skill-tooltip__status">
                          {isUnlocked ? (
                            <span className="skill-tooltip__unlocked">Unlocked</span>
                          ) : (
                            <>
                              <span className="skill-tooltip__locked">Locked</span>
                              <span className="skill-tooltip__req">Requires: {skill.unlockReq}</span>
                              <div className="skill-tooltip__progress">
                                <div className="skill-tooltip__progress-bar">
                                  <div
                                    className="skill-tooltip__progress-fill"
                                    style={{ width: `${progressPercent}%` }}
                                  />
                                </div>
                                <span className="skill-tooltip__progress-text">
                                  {progress.current}/{progress.target}
                                </span>
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="brain-overlay" onClick={handleBackdropClick}>
      <div ref={panelRef} className="brain-panel">
        {/* Close button */}
        <button className="brain-panel__close" onClick={onClose}>&times;</button>

        {loading ? (
          <div className="brain-panel__loading">Loading...</div>
        ) : error ? (
          <div className="brain-panel__error">{error}</div>
        ) : (
          <>
            {/* Header: Level and XP */}
            <header className="brain-header">
              <div className="brain-header__title">PAL</div>
              <div className="brain-header__level">Level {level}</div>
              <div className="brain-header__xp">
                <div className="xp-bar">
                  <div className="xp-bar__fill" style={{ width: `${(xp / xpToNext) * 100}%` }} />
                </div>
                <span className="xp-bar__text">{xp}/{xpToNext}</span>
              </div>

              {/* Evolution path */}
              <div className="evolution-path">
                {EVOLUTION_STAGES.map((stage, i) => (
                  <span
                    key={stage.name}
                    className={`evolution-stage ${i === evolution.index ? "evolution-stage--current" : ""} ${i < evolution.index ? "evolution-stage--past" : ""}`}
                  >
                    {stage.name}
                    {i < EVOLUTION_STAGES.length - 1 && <span className="evolution-arrow">&rarr;</span>}
                  </span>
                ))}
              </div>
            </header>

            {/* Tabs */}
            <nav className="brain-tabs">
              {(["overview", "skills", "knowledge", "thoughts"] as TabType[]).map((tab) => (
                <button
                  key={tab}
                  className={`brain-tab ${activeTab === tab ? "brain-tab--active" : ""}`}
                  onClick={() => { setActiveTab(tab); setSelectedSkill(null); }}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </nav>

            {/* Content */}
            <div className="brain-content">
              {activeTab === "overview" && (
                <div className="brain-overview">
                  {/* Stats */}
                  <div className="brain-stats">
                    <div className="brain-stat">
                      <span className="brain-stat__label">Bond</span>
                      <div className="brain-stat__bar">
                        <div className="brain-stat__fill" style={{ width: `${bond}%` }} />
                      </div>
                      <span className="brain-stat__value">{bond}</span>
                    </div>
                    <div className="brain-stat">
                      <span className="brain-stat__label">Knowledge</span>
                      <div className="brain-stat__bar">
                        <div className="brain-stat__fill" style={{ width: `${knowledge}%` }} />
                      </div>
                      <span className="brain-stat__value">{knowledge}</span>
                    </div>
                    <div className="brain-stat">
                      <span className="brain-stat__label">Memories</span>
                      <span className="brain-stat__number">{brain?.memory_count || 0}</span>
                    </div>
                    <div className="brain-stat">
                      <span className="brain-stat__label">Topics</span>
                      <span className="brain-stat__number">{Object.keys(topics).length}</span>
                    </div>
                  </div>

                  {/* Mini skill tree preview */}
                  <div className="brain-overview__skills">
                    <div className="brain-overview__skills-header">
                      <span>Skills</span>
                      <span className="brain-overview__skills-count">
                        {Object.values(skills).filter(s => s.unlocked).length}/{Object.keys(SKILL_TREE).length}
                      </span>
                    </div>
                    <div className="brain-overview__skills-preview">
                      {Object.entries(SKILL_TREE).slice(0, 6).map(([id, skill]) => {
                        const isUnlocked = skills[id]?.unlocked;
                        return (
                          <div
                            key={id}
                            className={`skill-preview ${isUnlocked ? "skill-preview--unlocked" : ""}`}
                          >
                            {skill.name}
                          </div>
                        );
                      })}
                    </div>
                    <button className="brain-overview__view-all" onClick={() => setActiveTab("skills")}>
                      View Skill Tree &rarr;
                    </button>
                  </div>
                </div>
              )}

              {activeTab === "skills" && renderSkillTree()}

              {activeTab === "knowledge" && (
                <div className="brain-knowledge">
                  {Object.keys(topics).length === 0 ? (
                    <div className="brain-empty">No topics learned yet</div>
                  ) : (
                    <>
                      <div className="knowledge-list">
                        {Object.entries(topics).map(([name, topic]: [string, Topic]) => {
                          const level = UNDERSTANDING_VALUES[topic.understanding] || 1;
                          return (
                            <div key={name} className="knowledge-item">
                              <span className="knowledge-item__name">{topic.display_name || name}</span>
                              <div className="knowledge-item__bar">
                                {[1, 2, 3, 4].map((i) => (
                                  <div
                                    key={i}
                                    className={`knowledge-item__segment ${i <= level ? "knowledge-item__segment--filled" : ""}`}
                                  />
                                ))}
                              </div>
                              <span className="knowledge-item__level">{topic.understanding}</span>
                            </div>
                          );
                        })}
                      </div>
                      {unresolvedCount > 0 && (
                        <div className="knowledge-unresolved">
                          Unresolved: {unresolvedCount}
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

              {activeTab === "thoughts" && (
                <div className="brain-thoughts">
                  {pendingThoughts.length === 0 && recentDreams.length === 0 ? (
                    <div className="brain-empty">No thoughts yet</div>
                  ) : (
                    <>
                      {pendingThoughts.length > 0 && (
                        <div className="thoughts-section">
                          <div className="thoughts-section__title">Pending thoughts</div>
                          <div className="thoughts-list">
                            {pendingThoughts.map((thought, i) => (
                              <div key={i} className="thought-item">"{thought.thought}"</div>
                            ))}
                          </div>
                        </div>
                      )}
                      {recentDreams.length > 0 && (
                        <div className="thoughts-section">
                          <div className="thoughts-section__title">Dreams</div>
                          <div className="thoughts-list">
                            {recentDreams.map((dream, i) => (
                              <div key={i} className="thought-item thought-item--dream">"{dream.dream}"</div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>

            {/* Footer with age */}
            {identity && (
              <footer className="brain-footer">
                {identity.age}
              </footer>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default BrainPanel;
