import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Header from "../components/Header/Header";
import "./CalculatorPage.css";

const SERVICE_CONFIG = {
  billboard: {
    label: "Білборди",
    title: "Калькулятор вартості білборда",
    subtitle:
      "Оцініть вартість розміщення зовнішньої реклами на білборді за кілька кліків.",
    previewTitle: "Адреса білборда",
    previewClass: "billboard-preview",
  },
  led: {
    label: "LED-екрани",
    title: "Калькулятор вартості LED-екрана",
    subtitle:
      "Оцініть вартість розміщення реклами на LED-екранах за кілька кліків.",
    previewTitle: "Адреса LED екрана",
    previewClass: "led-preview",
  },
  print: {
    label: "Поліграфія",
    title: "Калькулятор вартості друку",
    subtitle:
      "Розрахуйте приблизну вартість друку рекламної продукції для вашого бізнесу.",
    previewTitle: "Параметри друку",
    previewClass: "print-preview",
  },
};

const SCREEN_SIZES = {
  "3 × 6 м": 19000,
  "4 × 8 м": 23500,
  "5 × 10 м": 31000,
};

const LOCATIONS = {
  "м. Харків, вул. Сумська, 45": 1500,
  "м. Київ, просп. Перемоги, 21": 3000,
  "м. Львів, вул. Городоцька, 12": 2200,
};

const VIDEO_DURATION_PRICES = {
  5: 0,
  10: 2500,
  15: 4200,
  30: 7900,
};

const PRINT_TYPES = {
  Візитки: 7,
  Флаєри: 5,
  Буклети: 14,
  Плакати: 45,
};

const PRINT_MATERIALS = {
  "Крейдований папір": 1,
  "Щільний картон": 1.35,
  "Самоклеюча плівка": 1.8,
  Банер: 2.3,
};

const PRINT_SIZES = {
  "90 × 50 мм": 1,
  A5: 1.4,
  A4: 2,
  A3: 3.4,
};

const PRINT_COLORS = {
  "Чорно-білий": 0.75,
  "Кольоровий 4+0": 1,
  "Кольоровий 4+4": 1.35,
};

function formatMoney(value) {
  return `${Math.round(value).toLocaleString("uk-UA")} грн`;
}

function countDays(startDate, endDate) {
  const start = new Date(startDate);
  const end = new Date(endDate);

  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return 1;
  }

  const difference = end - start;
  const days = Math.ceil(difference / (1000 * 60 * 60 * 24));

  return Math.max(days, 1);
}

function CalculatorPage() {
  const { serviceType } = useParams();

  const currentType = SERVICE_CONFIG[serviceType] ? serviceType : "billboard";
  const config = SERVICE_CONFIG[currentType];

  const [form, setForm] = useState({
    screenSize: "3 × 6 м",
    location: "м. Харків, вул. Сумська, 45",
    startDate: "2024-05-20",
    endDate: "2024-05-27",
    videoDuration: 10,
    showCount: 100,
    needPosterPrint: false,

    printType: "Візитки",
    printQuantity: 500,
    printMaterial: "Крейдований папір",
    printSize: "90 × 50 мм",
    printColor: "Кольоровий 4+0",
  });

  const days = countDays(form.startDate, form.endDate);

  const calculation = useMemo(() => {
    if (currentType === "billboard") {
      const basePrice = SCREEN_SIZES[form.screenSize];
      const locationPrice = LOCATIONS[form.location];
      const periodPrice = days * 700;
      const posterPrintPrice = form.needPosterPrint ? 3500 : 0;

      return {
        rows: [
          ["Базова вартість", basePrice],
          [`Локація (${form.location})`, locationPrice],
          [`Період розміщення (${days} днів)`, periodPrice],
          ["Друк плаката", posterPrintPrice],
        ],
        total: basePrice + locationPrice + periodPrice + posterPrintPrice,
      };
    }

    if (currentType === "led") {
      const basePrice = SCREEN_SIZES[form.screenSize];
      const durationPrice = VIDEO_DURATION_PRICES[form.videoDuration];
      const locationPrice = LOCATIONS[form.location];
      const periodPrice = days * 250;
      const showCountPrice = Math.max(form.showCount - 100, 0) * 12;

      return {
        rows: [
          ["Базова вартість", basePrice],
          [`Тривалість ролика (${form.videoDuration} сек)`, durationPrice],
          [`Локація (${form.location})`, locationPrice],
          [`Період розміщення (${days} днів)`, periodPrice],
          [`Кількість показів (${form.showCount})`, showCountPrice],
        ],
        total:
          basePrice +
          durationPrice +
          locationPrice +
          periodPrice +
          showCountPrice,
      };
    }

    const unitPrice = PRINT_TYPES[form.printType];
    const materialMultiplier = PRINT_MATERIALS[form.printMaterial];
    const sizeMultiplier = PRINT_SIZES[form.printSize];
    const colorMultiplier = PRINT_COLORS[form.printColor];

    const rawTotal =
      unitPrice *
      form.printQuantity *
      materialMultiplier *
      sizeMultiplier *
      colorMultiplier;

    const discount =
      form.printQuantity >= 3000 ? 0.15 : form.printQuantity >= 1000 ? 0.1 : 0;

    const discountAmount = rawTotal * discount;

    return {
      rows: [
        [`Тип продукції (${form.printType})`, unitPrice * form.printQuantity],
        [`Матеріал (${form.printMaterial})`, rawTotal - unitPrice * form.printQuantity],
        [`Кількість (${form.printQuantity} шт.)`, 0],
        [`Знижка`, -discountAmount],
      ],
      total: rawTotal - discountAmount,
    };
  }, [currentType, form, days]);

  function updateField(fieldName, value) {
    setForm((previousForm) => ({
      ...previousForm,
      [fieldName]: value,
    }));
  }

  function handleSubmit(event) {
    event.preventDefault();

    alert(
      `Заявку на прорахунок створено. Орієнтовна сума: ${formatMoney(
        calculation.total
      )}`
    );
  }

  return (
    <div className="calculator-page">
      <Header />

      <main className="calculator-main">
        <section className="calculator-hero">
          <div>
            <div className="calculator-kicker">
              <span className="calculator-star">✦</span>
              <span>{config.label}</span>
            </div>

            <h1>{config.title}</h1>
            <p>{config.subtitle}</p>
          </div>

          <nav className="calculator-tabs" aria-label="Тип калькулятора">
            <Link
              className={currentType === "billboard" ? "active" : ""}
              to="/calculator/billboard"
            >
              Білборди
            </Link>

            <Link
              className={currentType === "led" ? "active" : ""}
              to="/calculator/led"
            >
              LED
            </Link>

            <Link
              className={currentType === "print" ? "active" : ""}
              to="/calculator/print"
            >
              Друк
            </Link>
          </nav>
        </section>

        <section className="calculator-layout">
          <form className="calculator-card" onSubmit={handleSubmit}>
            <div className="calculator-card-title">
              <span>☷</span>
              <h2>Параметри розміщення</h2>
            </div>

            {currentType !== "print" && (
              <>
                <label className="calculator-field">
                  <span>{currentType === "billboard" ? "Розмір білборда" : "Розмір екрана"}</span>
                  <select
                    value={form.screenSize}
                    onChange={(event) =>
                      updateField("screenSize", event.target.value)
                    }
                  >
                    {Object.keys(SCREEN_SIZES).map((size) => (
                      <option key={size} value={size}>
                        {size}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="calculator-field">
                  <span>Період бронювання</span>

                  <div className="calculator-date-row">
                    <input
                      type="date"
                      value={form.startDate}
                      onChange={(event) =>
                        updateField("startDate", event.target.value)
                      }
                    />

                    <span className="date-divider">—</span>

                    <input
                      type="date"
                      value={form.endDate}
                      onChange={(event) =>
                        updateField("endDate", event.target.value)
                      }
                    />
                  </div>
                </div>

                <label className="calculator-field">
                  <span>Локація</span>
                  <select
                    value={form.location}
                    onChange={(event) =>
                      updateField("location", event.target.value)
                    }
                  >
                    {Object.keys(LOCATIONS).map((location) => (
                      <option key={location} value={location}>
                        {location}
                      </option>
                    ))}
                  </select>
                </label>
              </>
            )}

            {currentType === "billboard" && (
              <label className="calculator-checkbox">
                <input
                  type="checkbox"
                  checked={form.needPosterPrint}
                  onChange={(event) =>
                    updateField("needPosterPrint", event.target.checked)
                  }
                />
                <span>Потрібен друк рекламного плаката</span>
              </label>
            )}

            {currentType === "led" && (
              <>
                <div className="calculator-field">
                  <span>Тривалість ролика</span>

                  <div className="calculator-segmented">
                    {[5, 10, 15, 30].map((seconds) => (
                      <button
                        key={seconds}
                        type="button"
                        className={
                          form.videoDuration === seconds ? "selected" : ""
                        }
                        onClick={() => updateField("videoDuration", seconds)}
                      >
                        {seconds} сек
                      </button>
                    ))}
                  </div>
                </div>

                <label className="calculator-field">
                  <span>Кількість показів</span>
                  <input
                    type="number"
                    min="1"
                    value={form.showCount}
                    onChange={(event) =>
                      updateField("showCount", Number(event.target.value))
                    }
                  />
                </label>
              </>
            )}

            {currentType === "print" && (
              <>
                <label className="calculator-field">
                  <span>Тип продукції</span>
                  <select
                    value={form.printType}
                    onChange={(event) =>
                      updateField("printType", event.target.value)
                    }
                  >
                    {Object.keys(PRINT_TYPES).map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="calculator-field">
                  <span>Кількість</span>
                  <input
                    type="number"
                    min="1"
                    value={form.printQuantity}
                    onChange={(event) =>
                      updateField("printQuantity", Number(event.target.value))
                    }
                  />
                </label>

                <label className="calculator-field">
                  <span>Матеріал</span>
                  <select
                    value={form.printMaterial}
                    onChange={(event) =>
                      updateField("printMaterial", event.target.value)
                    }
                  >
                    {Object.keys(PRINT_MATERIALS).map((material) => (
                      <option key={material} value={material}>
                        {material}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="calculator-field">
                  <span>Розмір</span>
                  <select
                    value={form.printSize}
                    onChange={(event) =>
                      updateField("printSize", event.target.value)
                    }
                  >
                    {Object.keys(PRINT_SIZES).map((size) => (
                      <option key={size} value={size}>
                        {size}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="calculator-field">
                  <span>Кольоровість</span>
                  <select
                    value={form.printColor}
                    onChange={(event) =>
                      updateField("printColor", event.target.value)
                    }
                  >
                    {Object.keys(PRINT_COLORS).map((color) => (
                      <option key={color} value={color}>
                        {color}
                      </option>
                    ))}
                  </select>
                </label>
              </>
            )}

            <div className="calculator-days-row">
              <span>{currentType === "print" ? "Формат" : "Кількість днів"}</span>
              <strong>
                {currentType === "print" ? form.printSize : `${days} днів`}
              </strong>
            </div>

            <div className="calculator-price-list">
              {calculation.rows.map(([label, price]) => (
                <div key={label}>
                  <span>{label}</span>
                  <strong>{formatMoney(price)}</strong>
                </div>
              ))}
            </div>

            <div className="calculator-total">
              <span>Підсумкова вартість</span>
              <strong>{formatMoney(calculation.total)}</strong>
            </div>

            <button className="calculator-submit" type="submit">
              Замовити прорахунок
              <span>→</span>
            </button>

            <p className="calculator-security">
              Ваші дані захищені та не передаються третім особам
            </p>
          </form>

          <aside className="calculator-preview-card">
            <div className={`calculator-visual ${config.previewClass}`}>
              <div className="visual-object" />
            </div>

            <div className="preview-info">
              <span className="preview-label">{config.previewTitle}</span>

              <h2>
                {currentType === "print"
                  ? `${form.printType}, ${form.printQuantity} шт.`
                  : form.location}
              </h2>

                <div className="preview-tags">
                    {currentType === "billboard" && (
                        <>
                        <span>Розмір: {form.screenSize}</span>
                        <span>
                            {form.startDate} — {form.endDate} ({days} днів)
                        </span>
                        </>
                    )}

                    {currentType === "led" && (
                        <>
                        <span>Розмір: {form.screenSize}</span>
                        <span>Тривалість: {form.videoDuration} сек</span>
                        <span>Показів: {form.showCount}</span>
                        <span>
                            {form.startDate} — {form.endDate} ({days} днів)
                        </span>
                        </>
                    )}

                    {currentType === "print" && (
                        <>
                        <span>Матеріал: {form.printMaterial}</span>
                        <span>Розмір: {form.printSize}</span>
                        <span>Колір: {form.printColor}</span>
                        </>
                    )}
                </div>

              <p className="preview-note">
                Зображення є ілюстративним. Остаточну суму підтвердить менеджер
                після уточнення деталей замовлення.
              </p>
            </div>
          </aside>
        </section>
      </main>
    </div>
  );
}

export default CalculatorPage;