import { useEffect, useRef } from "react";
import "./Menu.css";

type WindowMode = "full" | "widget" | "floating";

interface MenuProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectMode: (mode: WindowMode) => void;
  onOpenHistory: () => void;
  onOpenBrain: () => void;
  onOpenSettings: () => void;
  onHide: () => void;
  onQuit: () => void;
  currentMode?: WindowMode;
}

interface MenuItem {
  label: string;
  action: () => void;
  active?: boolean;
}

interface MenuSection {
  items: MenuItem[];
}

function Menu({
  isOpen,
  onClose,
  onSelectMode,
  onOpenHistory,
  onOpenBrain,
  onOpenSettings,
  onHide,
  onQuit,
  currentMode = "full",
}: MenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  // Close on click outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    // Delay to prevent immediate close from the same click that opened it
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

  const sections: MenuSection[] = [
    {
      items: [
        { label: "Full window", action: () => onSelectMode("full"), active: currentMode === "full" },
        { label: "Widget mode", action: () => onSelectMode("widget"), active: currentMode === "widget" },
        { label: "Floating mode", action: () => onSelectMode("floating"), active: currentMode === "floating" },
      ],
    },
    {
      items: [
        { label: "History", action: onOpenHistory },
        { label: "Pal's Brain", action: onOpenBrain },
        { label: "Settings", action: onOpenSettings },
      ],
    },
    {
      items: [
        { label: "Hide for 1 hour", action: onHide },
        { label: "Quit", action: onQuit },
      ],
    },
  ];

  const handleItemClick = (action: () => void) => {
    action();
    onClose();
  };

  return (
    <div className="menu" ref={menuRef}>
      <div className="menu__content">
        {sections.map((section, sectionIndex) => (
          <div key={sectionIndex} className="menu__section">
            {section.items.map((item, itemIndex) => (
              <button
                key={itemIndex}
                className={`menu__item ${item.active ? "menu__item--active" : ""}`}
                onClick={() => handleItemClick(item.action)}
              >
                {item.label}
                {item.active && <span className="menu__check">✓</span>}
              </button>
            ))}
            {sectionIndex < sections.length - 1 && <div className="menu__divider" />}
          </div>
        ))}
      </div>
    </div>
  );
}

export default Menu;
