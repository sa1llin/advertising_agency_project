import { Link } from "react-router-dom";
import "./MediaSection.css";

function MediaSection({ services }) {
  return (
    <section className="media-showcase" id="media">
      <div className="media-showcase__header">
        <h2 className="media-showcase__title">
          <span className="media-showcase__title-icon">✦</span>
          НАШІ НОСІЇ
        </h2>

        <a className="media-showcase__details" href="#rent">
          <span className="media-showcase__details-dot"></span>
          <span>Обрати формат реклами</span>
          <span className="media-showcase__details-line"></span>
          <span className="media-showcase__details-arrow">↗</span>
        </a>
      </div>

      <div className="media-showcase__grid">
        {services.map((service) => (
          <Link
            key={service.id}
            to={service.calculatorPath}
            className="media-card-link"
            aria-label={`Перейти до калькулятора: ${service.title}`}
          >
            <article className="media-card">
              <div className="media-card__top">
                <div className="media-card__heading">
                  <span className="media-card__number">{service.number}</span>
                  <h3 className="media-card__title">{service.title}</h3>
                </div>

                <span className="media-card__label">{service.label}</span>
              </div>

              <div className="media-card__image-wrap">
                <img
                  className="media-card__image"
                  src={service.image}
                  alt={service.title}
                />
              </div>

              <div className="media-card__bottom">
                <p className="media-card__description">
                  {service.description}
                </p>

                <span className="media-card__button" aria-hidden="true">
                  ↗
                </span>
              </div>
            </article>
          </Link>
        ))}
      </div>
    </section>
  );
}

export default MediaSection;