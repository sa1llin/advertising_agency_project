import { useState } from "react";
import { images } from "../../assets/images";
import "./Header.css";

function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const menuItems = [
    { title: "ПРО НАС", href: "#about" },
    { title: "НАШІ НОСІЇ", href: "#media" },
    { title: "КРЕАТИВ ТА ДИЗАЙН", href: "#creative" },
    { title: "ОРЕНДА", href: "#rent" },
    { title: "ДРУК", href: "#print" },
    { title: "FAQ", href: "#faq" },
  ];

  return (
    <header className="agency-header">
      <a className="agency-header__logo" href="/">
        <img src={images.logo} alt="Creative Spark Agency" />
      </a>

      <nav
        className={
          isMenuOpen
            ? "agency-header__nav agency-header__nav--open"
            : "agency-header__nav"
        }
      >
        {menuItems.map((item) => (
          <a
            key={item.title}
            href={item.href}
            onClick={() => setIsMenuOpen(false)}
          >
            {item.title}
          </a>
        ))}
      </nav>

      <div className="agency-header__actions">
        <a className="agency-header__external-link" href="#contacts">
          ↗
        </a>

        <a className="agency-header__phone" href="tel:+3809999911">
          <span>(099) 999 11</span>
          <span className="agency-header__phone-icon">☎</span>
        </a>

        <button
          className="agency-header__burger"
          type="button"
          onClick={() => setIsMenuOpen((prev) => !prev)}
          aria-label="Відкрити меню"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
      </div>
    </header>
  );
}

export default Header;