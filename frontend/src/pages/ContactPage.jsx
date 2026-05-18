import { Link, useLocation } from "react-router-dom";
import { images } from "../assets/images";
import "./ContactPage.css";

const SERVICE_LABELS = {
  billboard: "Білборди",
  led: "LED-екрани",
  print: "Поліграфія",
};

function ContactPage() {
  const { state } = useLocation();

  const serviceName = state?.serviceType
    ? SERVICE_LABELS[state.serviceType] || "Послуга"
    : "";

  function handleSubmit(event) {
    event.preventDefault();

    const formData = new FormData(event.currentTarget);
    const contactRequest = {
      name: formData.get("name"),
      phone: formData.get("phone"),
      email: formData.get("email"),
      message: formData.get("message"),
      service: serviceName,
      total: state?.total || null,
    };

    console.log("Contact request:", contactRequest);
    alert("Дякуємо! Ваш контакт отримано. Менеджер зв'яжеться з вами найближчим часом.");

    event.currentTarget.reset();
  }

  return (
    <main className="contact-page">
      <section className="contact-card" aria-labelledby="contact-title">
        <div className="contact-card__top">
          <Link className="contact-logo" to="/" aria-label="На головну">
            <img src={images.logo} alt="Creative Spark Agency" />
          </Link>

          <Link className="contact-close" to="/" aria-label="Закрити форму">
            ×
          </Link>
        </div>

        <img className="contact-star" src={images.heroStar} alt="" aria-hidden="true" />
        <span className="contact-spark" aria-hidden="true">✧</span>
        <span className="contact-orbit" aria-hidden="true"></span>

        <div className="contact-intro">
          <h1 id="contact-title">Залишай контакт</h1>
          <p>Ми зв'яжемось і допоможемо зрозуміти, що підійде саме тобі!</p>
        </div>

        <form className="contact-form" onSubmit={handleSubmit}>
          <label className="contact-field">
            <span>Ім'я</span>
            <input
              type="text"
              name="name"
              placeholder="Введи своє ім'я"
              autoComplete="name"
              required
            />
          </label>

          <label className="contact-field">
            <span>Контактний номер</span>
            <input
              type="tel"
              name="phone"
              placeholder="+38 069 12* ** **"
              autoComplete="tel"
              required
            />
          </label>

          <label className="contact-field">
            <span>Електронна скринька</span>
            <input
              type="email"
              name="email"
              placeholder="Введи свій e-mail"
              autoComplete="email"
              required
            />
          </label>

          <label className="contact-field contact-field--message">
            <span>Повідомлення</span>
            <textarea
              name="message"
              placeholder={
                serviceName
                  ? `Твій коментар: ${serviceName}`
                  : "Твій коментар"
              }
              rows="5"
            ></textarea>
            <small>*Необов'язково</small>
          </label>

          <div className="contact-form__bottom">
            <label className="contact-consent">
              <input type="checkbox" required />
              <span>
                Я прочитав та погоджуюсь з <a href="#rules">Правилами використання</a> та{" "}
                <a href="#privacy">Політикою конфіденційності</a>
              </span>
            </label>

            <button className="contact-submit" type="submit">
              Надіслати
              <span>→</span>
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}

export default ContactPage;
