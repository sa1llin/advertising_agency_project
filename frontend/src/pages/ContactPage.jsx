import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { images } from "../assets/images";
import "./ContactPage.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const SERVICE_LABELS = {
  billboard: "Білборди",
  led: "LED-екрани",
  print: "Поліграфія",
};

const SERVICE_TYPES = {
  billboard: "billboard",
  led: "led",
  print: "printing",
};

function ContactPage() {
  const { state } = useLocation();
  const [isSending, setIsSending] = useState(false);
  const [formStatus, setFormStatus] = useState(null);
  const initialServiceType = SERVICE_TYPES[state?.serviceType] || "";
  const hasCalculatorData =
    state?.source === "calculator" &&
    state?.calculationData?.service_type === initialServiceType;

  const serviceName = state?.serviceType
    ? SERVICE_LABELS[state.serviceType] || "Послуга"
    : "";

  async function handleSubmit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    setIsSending(true);
    setFormStatus(null);

    try {
      const response = await fetch(`${API_BASE_URL}/applications/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          full_name: formData.get("name"),
          phone: formData.get("phone"),
          email: formData.get("email"),
          service_type: formData.get("service_type") || "other",
          source: hasCalculatorData ? "calculator" : "contact",
          calculation_data: hasCalculatorData
            ? state.calculationData
            : null,
          comment: formData.get("message") || null,
        }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(
          typeof payload?.detail === "string"
            ? payload.detail
            : "Не вдалося надіслати заявку.",
        );
      }

      form.reset();
      setFormStatus({
        type: "success",
        message:
          "Дякуємо! Заявку отримано. Менеджер зв'яжеться з вами найближчим часом.",
      });
    } catch (error) {
      setFormStatus({
        type: "error",
        message:
          error instanceof Error
            ? error.message
            : "Не вдалося надіслати заявку.",
      });
    } finally {
      setIsSending(false);
    }
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

        <img
          className="contact-star"
          src={images.heroStar}
          alt=""
          aria-hidden="true"
        />
        <span className="contact-spark" aria-hidden="true">
          ✧
        </span>
        <span className="contact-orbit" aria-hidden="true"></span>

        <div className="contact-intro">
          <h1 id="contact-title">Залишай контакт</h1>
          <p>
            Ми зв&apos;яжемось і допоможемо зрозуміти, що підійде саме тобі!
          </p>
        </div>

        <form className="contact-form" onSubmit={handleSubmit}>
          <label className="contact-field">
            <span>Ім&apos;я</span>
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

          <label className="contact-field">
            <span>Послуга</span>
            <select
              name={hasCalculatorData ? undefined : "service_type"}
              defaultValue={initialServiceType}
              disabled={hasCalculatorData}
            >
              <option value="">Не обрано — звичайна заявка</option>
              <option value="billboard">Білборд</option>
              <option value="led">LED-екран</option>
              <option value="printing">Друк</option>
            </select>
            {hasCalculatorData && (
              <input
                type="hidden"
                name="service_type"
                value={initialServiceType}
              />
            )}
          </label>

          {hasCalculatorData && (
            <p className="contact-form__calculation-note">
              До заявки буде додано параметри та орієнтовну вартість із
              калькулятора {serviceName}.
            </p>
          )}

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
            <small>*Необов&apos;язково</small>
          </label>

          {formStatus && (
            <p
              className={`contact-form__status contact-form__status--${formStatus.type}`}
              role={formStatus.type === "error" ? "alert" : "status"}
            >
              {formStatus.message}
            </p>
          )}

          <div className="contact-form__bottom">
            <button
              className="contact-submit"
              type="submit"
              disabled={isSending}
            >
              {isSending ? "Надсилання..." : "Надіслати"}
              <span>→</span>
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}

export default ContactPage;
