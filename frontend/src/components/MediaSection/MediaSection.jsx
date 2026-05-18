import { images } from "../../assets/images";
import "./MediaSection.css";

function MediaSection() {
  const services = [
    {
      id: "billboards",
      number: "01",
      title: "ЗОВНІШНЯ РЕКЛАМА",
      label: "OOH",
      image: images.oohImage,
      imageAlt: "Білборд для зовнішньої реклами",
      description: "Білборди / сітілайти / рекламні конструкції",
    },
    {
      id: "led",
      number: "02",
      title: "ЦИФРОВА ЗОВНІШНЯ РЕКЛАМА",
      label: "DOOH",
      image: images.doohImage,
      imageAlt: "LED-екран для цифрової зовнішньої реклами",
      description: "LED-екрани / медіафасади / цифрові площини",
    },
    {
      id: "print",
      number: "03",
      title: "ДРУК",
      label: "PRINT",
      image: images.printImage,
      imageAlt: "Друкована рекламна продукція",
      description: "Поліграфія / брендована продукція / рекламний друк",
    },
  ];

  return (
    <section className="media-showcase" id="media">
      <div className="media-showcase__header">
        <h2 className="media-showcase__title">
          <span className="media-showcase__title-icon">✦</span>
          НАШІ НОСІЇ
        </h2>

        <a className="media-showcase__details" href="#media-details">
          <span className="media-showcase__details-dot"></span>
          <span className="media-showcase__details-text">ДЕТАЛЬНІШЕ</span>
          <span className="media-showcase__details-line"></span>
          <span className="media-showcase__details-arrow">→</span>
        </a>
      </div>

      <div className="media-showcase__grid">
        {services.map((service) => (
          <article className="media-card" key={service.id}>
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
                alt={service.imageAlt}
              />
            </div>

            <div className="media-card__bottom">
              <p className="media-card__description">{service.description}</p>

              <button
                className="media-card__button"
                type="button"
                aria-label={`Перейти до послуги: ${service.title}`}
              >
                →
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default MediaSection;