import { images } from "../assets/images";
import Header from "../components/Header/Header";
import "./HomePage.css";

function HomePage() {
  const services = [
    {
      id: 1,
      number: "01",
      title: "ЗОВНІШНЯ РЕКЛАМА",
      label: "OOH",
      image: images.oohImage,
      description: "Білборди та рекламні конструкції для розміщення зовнішньої реклами.",
    },
    {
      id: 2,
      number: "02",
      title: "ЦИФРОВА ЗОВНІШНЯ РЕКЛАМА",
      label: "DOOH",
      image: images.doohImage,
      description: "LED-екрани для динамічного рекламного контенту.",
    },
    {
      id: 3,
      number: "03",
      title: "ДРУК",
      label: "PRINT",
      image: images.printImage,
      description: "Друкована продукція для бізнесу, подій та рекламних кампаній.",
    },
  ];

  return (
    <div className="home-page">
      <Header />
      <main>
        <section className="hero-section">
          <div className="hero-content">
            <h1>
              МИ СТВОРЮЄМО СТРАТЕГІЇ, КРЕАТИВ І УНІКАЛЬНІ КОНСТРУКЦІЇ, А ЩЕ —
              РОЗМІЩУЄМО РЕКЛАМУ НА НОСІЯХ, ЩОБ БРЕНДИ НЕ ПРОСТО З’ЯВЛЯЛИСЯ,
              А ЗАПАМ&apos;ЯТ
              <span className="text-star">✺</span>
              ВУВАЛИСЯ
            </h1>

            <div className="hero-line"></div>

            <p>
              Повний цикл рекламних рішень: від ідеї та креативу до виробництва
              і розміщення на найефективніших носіях.
            </p>
          </div>

          <div className="hero-image">
            <img src={images.heroStar} alt="Decorative 3D star" />
          </div>
        </section>

        <section className="media-section" id="media">
          <div className="section-header">
            <h2>
              <span>✦</span>
              НАШІ НОСІЇ
            </h2>

            <a href="#media-details" className="details-link">
              <span className="details-dot"></span>
              ДЕТАЛЬНІШЕ
              <span className="details-line"></span>
              <span className="details-arrow">→</span>
            </a>
          </div>

          <div className="services-grid">
            {services.map((service) => (
              <article className="service-card" key={service.id}>
                <div className="service-card-top">
                  <div className="service-title-group">
                    <span className="service-number">{service.number}</span>
                    <h3>{service.title}</h3>
                  </div>

                  <span className="service-label">{service.label}</span>
                </div>

                <div className="service-image">
                  <img src={service.image} alt={service.title} />
                </div>

                <div className="service-card-bottom">
                  <p>{service.description}</p>

                  <button type="button" className="service-button">
                    →
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

export default HomePage;