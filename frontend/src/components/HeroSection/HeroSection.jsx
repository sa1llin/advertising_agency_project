import { images } from "../../assets/images";
import "./HeroSection.css";

function HeroSection() {
  return (
    <section className="hero">
      <div className="hero__content">
        <h1 className="hero__title">
          МИ СТВОРЮЄМО СТРАТЕГІЇ, КРЕАТИВ І УНІКАЛЬНІ КОНСТРУКЦІЇ, А ЩЕ —
          РОЗМІЩУЄМО РЕКЛАМУ НА НОСІЯХ, ЩОБ БРЕНДИ НЕ ПРОСТО З’ЯВЛЯЛИСЯ, А
          ЗАПАМ’ЯТОВУВАЛИСЯ
        </h1>

        <div className="hero__divider"></div>

        <p className="hero__description">
          Повний цикл рекламних рішень: від ідеї та креативу до виробництва і
          розміщення на найефективніших носіях.
        </p>
      </div>

      <div className="hero__image-wrapper">
        <img
          className="hero__image"
          src={images.heroStar}
          alt="Декоративна 3D-зірка"
        />
      </div>
    </section>
  );
}

export default HeroSection;