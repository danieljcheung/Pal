import { useState, useEffect, useRef } from "react";
import { fetchBrain, fetchIdentity, type Brain, type Identity, type Topic } from "../api";
import "./BrainPanel.css";

interface BrainPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

// Skill display names and unlock conditions for progress display
const SKILL_INFO: Record<string, { name: string; requirement: string; getProgress: (stats: Brain["stats"]) => { current: number; target: number } }> = {
  greet: {
    name: "Greeting",
    requirement: "10 check-ins",
    getProgress: (stats) => ({ current: stats.check_ins || 0, target: 10 }),
  },
  recall: {
    name: "Active Recall",
    requirement: "25 memories",
    getProgress: (stats) => ({ current: stats.memories_stored || 0, target: 25 }),
  },
  remind: {
    name: "Reminders",
    requirement: "5 reminder requests",
    getProgress: (stats) => ({ current: stats.reminders_requested || 0, target: 5 }),
  },
  time_sense: {
    name: "Time Sense",
    requirement: "50 messages, 3 days",
    getProgress: (stats) => ({ current: stats.messages_exchanged || 0, target: 50 }),
  },
  notice_patterns: {
    name: "Pattern Recognition",
    requirement: "50 memories, 10 shares",
    getProgress: (stats) => ({ current: stats.memories_stored || 0, target: 50 }),
  },
  hold_thoughts: {
    name: "Hold Thoughts",
    requirement: "20 thought dumps",
    getProgress: (stats) => ({ current: stats.thought_dumps || 0, target: 20 }),
  },
  opinions: {
    name: "Opinions",
    requirement: "100 messages, 10 corrections",
    getProgress: (stats) => ({ current: stats.messages_exchanged || 0, target: 100 }),
  },
  research: {
    name: "Research",
    requirement: "3 topics with questions",
    getProgress: () => ({ current: 0, target: 3 }),
  },
  tasks: {
    name: "Task Tracking",
    requirement: "5 reminders delivered",
    getProgress: (stats) => ({ current: stats.reminders_delivered || 0, target: 5 }),
  },
  summarize: {
    name: "Summarize",
    requirement: "100 memories",
    getProgress: (stats) => ({ current: stats.memories_stored || 0, target: 100 }),
  },
  concern: {
    name: "Show Concern",
    requirement: "10 emotional shares",
    getProgress: (stats) => ({ current: stats.emotional_shares || 0, target: 10 }),
  },
};

// Understanding level values for progress bar
const UNDERSTANDING_LEVELS: Record<string, number> = {
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
  const panelRef = useRef<HTMLDivElement>(null);

  // Fetch brain data when panel opens
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
        setError("Could not load brain data");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [isOpen]);

  // Close on click outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    const timer = setTimeout(() => {
      document.addEventListener("click", handleClickOutside);
    }, 10);

    return () => {
      clearTimeout(timer);
      document.removeEventListener("click", handleClickOutside);
    };
  }, [isOpen, onClose]);

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

  if (!isOpen) return null;

  const stats = brain?.stats;
  const skills = brain?.skills || {};
  const topics = brain?.topics || {};
  const innerLife = brain?.inner_life;

  // Count topics learned
  const topicsCount = Object.keys(topics).length;

  // Get unlocked and locked skills
  const unlockedSkills = Object.entries(skills).filter(([, data]) => data.unlocked);
  const lockedSkills = Object.entries(skills).filter(([, data]) => !data.unlocked);

  // Get pending thoughts
  const pendingThoughts = innerLife?.thought_queue?.filter(t => !t.surfaced) || [];

  // Get recent dreams
  const recentDreams = innerLife?.dream_journal?.slice(-3) || [];

  // Extract preferences from topics (likes/dislikes would be stored as special topics)
  // For now, we'll show a placeholder since preferences aren't explicitly stored
  const likes: string[] = [];
  const dislikes: string[] = [];

  return (
    <>
      {/* Backdrop */}
      <div className={`brain-panel__backdrop ${isOpen ? "brain-panel__backdrop--visible" : ""}`} />

      {/* Panel */}
      <div
        ref={panelRef}
        className={`brain-panel ${isOpen ? "brain-panel--open" : ""}`}
      >
        {/* Header */}
        <div className="brain-panel__header">
          <div className="brain-panel__title">
            <span className="brain-panel__title-text">Pal's Brain</span>
            {identity && (
              <span className="brain-panel__age">{identity.age}</span>
            )}
          </div>
          <button className="brain-panel__close" onClick={onClose}>
            &times;
          </button>
        </div>

        {/* Content */}
        <div className="brain-panel__content">
          {loading ? (
            <div className="brain-panel__loading">Loading...</div>
          ) : error ? (
            <div className="brain-panel__error">{error}</div>
          ) : (
            <>
              {/* Stats Section */}
              <section className="brain-panel__section">
                <h3 className="brain-panel__section-title">Stats</h3>
                <div className="brain-panel__stats">
                  <div className="brain-panel__stat">
                    <span className="brain-panel__stat-value">{stats?.messages_exchanged || 0}</span>
                    <span className="brain-panel__stat-label">Messages</span>
                  </div>
                  <div className="brain-panel__stat">
                    <span className="brain-panel__stat-value">{brain?.memory_count || 0}</span>
                    <span className="brain-panel__stat-label">Memories</span>
                  </div>
                  <div className="brain-panel__stat">
                    <span className="brain-panel__stat-value">{topicsCount}</span>
                    <span className="brain-panel__stat-label">Topics</span>
                  </div>
                  <div className="brain-panel__stat">
                    <span className="brain-panel__stat-value">{stats?.check_ins || 0}</span>
                    <span className="brain-panel__stat-label">Check-ins</span>
                  </div>
                </div>
              </section>

              {/* Skills Section */}
              <section className="brain-panel__section">
                <h3 className="brain-panel__section-title">Skills</h3>
                <div className="brain-panel__skills">
                  {/* Unlocked skills */}
                  {unlockedSkills.map(([name, data]) => (
                    <div key={name} className="brain-panel__skill brain-panel__skill--unlocked">
                      <span className="brain-panel__skill-icon">&#10003;</span>
                      <span className="brain-panel__skill-name">
                        {SKILL_INFO[name]?.name || name}
                      </span>
                      <span className="brain-panel__skill-level">Lv.{data.level}</span>
                    </div>
                  ))}

                  {/* Locked skills with progress */}
                  {lockedSkills.map(([name]) => {
                    const info = SKILL_INFO[name];
                    const progress = info?.getProgress(stats || {} as Brain["stats"]);
                    const progressPercent = progress
                      ? Math.min(100, Math.round((progress.current / progress.target) * 100))
                      : 0;

                    return (
                      <div key={name} className="brain-panel__skill brain-panel__skill--locked">
                        <span className="brain-panel__skill-icon">&#9675;</span>
                        <div className="brain-panel__skill-info">
                          <span className="brain-panel__skill-name">
                            {info?.name || name}
                          </span>
                          {progress && progress.current > 0 && (
                            <div className="brain-panel__skill-progress">
                              <div
                                className="brain-panel__skill-progress-bar"
                                style={{ width: `${progressPercent}%` }}
                              />
                              <span className="brain-panel__skill-progress-text">
                                {progress.current}/{progress.target}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>

              {/* Topics Section */}
              {topicsCount > 0 && (
                <section className="brain-panel__section">
                  <h3 className="brain-panel__section-title">Topics</h3>
                  <div className="brain-panel__topics">
                    {Object.entries(topics).map(([name, topicData]: [string, Topic]) => {
                      const level = UNDERSTANDING_LEVELS[topicData.understanding] || 1;
                      const unresolvedCount = topicData.unresolved?.length || 0;

                      return (
                        <div key={name} className="brain-panel__topic">
                          <div className="brain-panel__topic-header">
                            <span className="brain-panel__topic-name">
                              {topicData.display_name || name}
                            </span>
                            {unresolvedCount > 0 && (
                              <span className="brain-panel__topic-questions">
                                {unresolvedCount} ?
                              </span>
                            )}
                          </div>
                          <div className="brain-panel__topic-level">
                            <div className="brain-panel__topic-level-bar">
                              {[1, 2, 3, 4].map((i) => (
                                <div
                                  key={i}
                                  className={`brain-panel__topic-level-segment ${
                                    i <= level ? "brain-panel__topic-level-segment--filled" : ""
                                  }`}
                                />
                              ))}
                            </div>
                            <span className="brain-panel__topic-level-label">
                              {topicData.understanding}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>
              )}

              {/* Inner Life Section */}
              {(pendingThoughts.length > 0 || recentDreams.length > 0) && (
                <section className="brain-panel__section">
                  <h3 className="brain-panel__section-title">Inner Life</h3>

                  {pendingThoughts.length > 0 && (
                    <div className="brain-panel__inner-subsection">
                      <h4 className="brain-panel__subsection-title">Pending Thoughts</h4>
                      <div className="brain-panel__thoughts">
                        {pendingThoughts.slice(0, 3).map((thought, i) => (
                          <div key={i} className="brain-panel__thought">
                            "{thought.thought}"
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {recentDreams.length > 0 && (
                    <div className="brain-panel__inner-subsection">
                      <h4 className="brain-panel__subsection-title">Recent Dreams</h4>
                      <div className="brain-panel__dreams">
                        {recentDreams.map((dream, i) => (
                          <div key={i} className="brain-panel__dream">
                            "{dream.dream}"
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </section>
              )}

              {/* Preferences Section */}
              {(likes.length > 0 || dislikes.length > 0) && (
                <section className="brain-panel__section">
                  <h3 className="brain-panel__section-title">Preferences</h3>
                  {likes.length > 0 && (
                    <div className="brain-panel__preferences">
                      <span className="brain-panel__pref-label">Likes:</span>
                      <span className="brain-panel__pref-list">{likes.join(", ")}</span>
                    </div>
                  )}
                  {dislikes.length > 0 && (
                    <div className="brain-panel__preferences">
                      <span className="brain-panel__pref-label">Dislikes:</span>
                      <span className="brain-panel__pref-list">{dislikes.join(", ")}</span>
                    </div>
                  )}
                </section>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}

export default BrainPanel;
