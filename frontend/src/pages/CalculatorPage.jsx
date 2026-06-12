import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Header from "../components/Header/Header";
import "./CalculatorPage.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

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

function isoDate(date) {
  const offset = date.getTimezoneOffset();
  return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 10);
}

function initialDates() {
  const start = new Date();
  const end = new Date(start);
  end.setDate(end.getDate() + 7);
  return {
    startDate: isoDate(start),
    endDate: isoDate(end),
  };
}

function formatMoney(value) {
  return `${Math.round(value).toLocaleString("uk-UA")} грн`;
}

function countDays(startDate, endDate) {
  const start = new Date(`${startDate}T00:00:00`);
  const end = new Date(`${endDate}T00:00:00`);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return 0;
  }
  return Math.max(Math.round((end - start) / 86_400_000) + 1, 0);
}

function findPrice(pricesByCategory, category, code) {
  const items = pricesByCategory[category] || [];
  return items.find((item) => item.code === code) || items[0];
}

function CalculatorPage() {
  const { serviceType } = useParams();
  const navigate = useNavigate();
  const currentType = SERVICE_CONFIG[serviceType] ? serviceType : "billboard";
  const config = SERVICE_CONFIG[currentType];

  const [catalog, setCatalog] = useState({
    advertising_spaces: [],
    pricing_items: [],
  });
  const [catalogError, setCatalogError] = useState("");
  const [isLoadingCatalog, setIsLoadingCatalog] = useState(true);
  const [form, setForm] = useState(() => ({
    advertisingSpaceId: "",
    ...initialDates(),
    videoDuration: 10,
    showCount: 100,
    needPosterPrint: false,
    productType: "",
    printQuantity: 500,
    materialCode: "",
    sizeCode: "",
    colorMode: "",
  }));

  useEffect(() => {
    const controller = new AbortController();

    async function loadCatalog() {
      try {
        const response = await fetch(
          `${API_BASE_URL}/catalog/public-order-options`,
          { signal: controller.signal },
        );
        if (!response.ok) {
          throw new Error("Не вдалося завантажити ціни та рекламні площини.");
        }
        const payload = await response.json();
        setCatalog(payload);
        setCatalogError("");
      } catch (error) {
        if (error.name !== "AbortError") {
          setCatalogError(error.message || "Не вдалося завантажити каталог.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsLoadingCatalog(false);
        }
      }
    }

    loadCatalog();
    return () => controller.abort();
  }, []);

  const spaces = useMemo(
    () =>
      catalog.advertising_spaces.filter(
        (space) =>
          space.space_type === (currentType === "print" ? "" : currentType),
      ),
    [catalog.advertising_spaces, currentType],
  );

  const pricesByCategory = useMemo(() => {
    const result = {};
    for (const item of catalog.pricing_items) {
      if (!result[item.category]) {
        result[item.category] = [];
      }
      result[item.category].push(item);
    }
    return result;
  }, [catalog.pricing_items]);

  const selectedSpace =
    spaces.find(
      (space) => String(space.id) === String(form.advertisingSpaceId),
    ) || spaces[0];
  const days = countDays(form.startDate, form.endDate);

  const selectedProduct = findPrice(
    pricesByCategory,
    "print_product",
    form.productType,
  );
  const selectedMaterial = findPrice(
    pricesByCategory,
    "print_material",
    form.materialCode,
  );
  const selectedSize = findPrice(
    pricesByCategory,
    "print_size",
    form.sizeCode,
  );
  const selectedColor = findPrice(
    pricesByCategory,
    "print_color",
    form.colorMode,
  );

  const calculation = useMemo(() => {
    if (currentType === "billboard") {
      if (!selectedSpace || days < 1) {
        return { ready: false, rows: [], total: 0 };
      }
      const rental = Number(selectedSpace.base_price) * days;
      const printItem = (pricesByCategory.billboard_print || []).find(
        (item) => item.code === selectedSpace.size,
      );
      const printing = form.needPosterPrint
        ? Number(printItem?.amount || 0)
        : 0;
      return {
        ready: true,
        rows: [
          [`Оренда (${days} днів)`, rental],
          ["Друк плаката", printing],
        ],
        total: rental + printing,
      };
    }

    if (currentType === "led") {
      if (!selectedSpace || days < 1) {
        return { ready: false, rows: [], total: 0 };
      }
      const placement =
        Number(selectedSpace.base_price) *
        days *
        form.videoDuration *
        form.showCount;
      return {
        ready: true,
        rows: [
          [
            `${form.videoDuration} сек × ${form.showCount} показів × ${days} днів`,
            placement,
          ],
        ],
        total: placement,
      };
    }

    const product = selectedProduct;
    const material = selectedMaterial;
    const size = selectedSize;
    const color = selectedColor;
    if (!product || !material || !size || !color || form.printQuantity < 1) {
      return { ready: false, rows: [], total: 0 };
    }
    const rows = [
      [product.label, Number(product.amount) * form.printQuantity],
      [material.label, Number(material.amount) * form.printQuantity],
      [size.label, Number(size.amount) * form.printQuantity],
      [color.label, Number(color.amount) * form.printQuantity],
    ];
    return {
      ready: true,
      rows,
      total: rows.reduce((sum, row) => sum + row[1], 0),
    };
  }, [
    currentType,
    days,
    form.needPosterPrint,
    form.printQuantity,
    form.showCount,
    form.videoDuration,
    pricesByCategory,
    selectedColor,
    selectedMaterial,
    selectedProduct,
    selectedSpace,
    selectedSize,
  ]);

  function updateField(fieldName, value) {
    setForm((previous) => ({
      ...previous,
      [fieldName]: value,
    }));
  }

  function buildCalculationData() {
    const priceRows = calculation.rows.map(([label, amount]) => ({
      label,
      amount,
    }));

    if (currentType === "billboard") {
      return {
        service_type: "billboard",
        advertising_space_id: selectedSpace.id,
        location: selectedSpace.location,
        size: selectedSpace.size,
        period_start: form.startDate,
        period_end: form.endDate,
        days,
        need_printing: form.needPosterPrint,
        estimated_total: calculation.total,
        price_rows: priceRows,
      };
    }

    if (currentType === "led") {
      return {
        service_type: "led",
        advertising_space_id: selectedSpace.id,
        location: selectedSpace.location,
        size: selectedSpace.size,
        period_start: form.startDate,
        period_end: form.endDate,
        days,
        video_seconds: form.videoDuration,
        impressions_per_day: form.showCount,
        estimated_total: calculation.total,
        price_rows: priceRows,
      };
    }

    return {
      service_type: "printing",
      product_type: selectedProduct.code,
      product_name: selectedProduct.label,
      material_code: selectedMaterial.code,
      material_name: selectedMaterial.label,
      size_code: selectedSize.code,
      size_name: selectedSize.label,
      color_mode: selectedColor.code,
      color_name: selectedColor.label,
      quantity: form.printQuantity,
      estimated_total: calculation.total,
      price_rows: priceRows,
    };
  }

  function handleSubmit(event) {
    event.preventDefault();
    if (!calculation.ready) {
      return;
    }
    navigate("/contact", {
      state: {
        source: "calculator",
        serviceType: currentType,
        calculationData: buildCalculationData(),
      },
    });
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

            {isLoadingCatalog && (
              <p className="calculator-security">Завантаження цін з БД...</p>
            )}
            {catalogError && (
              <p className="calculator-security">{catalogError}</p>
            )}

            {currentType !== "print" && (
              <>
                <label className="calculator-field">
                  <span>
                    {currentType === "billboard"
                      ? "Адреса білборда"
                      : "Адреса LED-екрана"}
                  </span>
                  <select
                    value={selectedSpace?.id || ""}
                    onChange={(event) =>
                      updateField(
                        "advertisingSpaceId",
                        Number(event.target.value),
                      )
                    }
                  >
                    {spaces.map((space) => (
                      <option key={space.id} value={space.id}>
                        {space.location} ({space.size || "розмір не вказано"})
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
                      min={form.startDate}
                      value={form.endDate}
                      onChange={(event) =>
                        updateField("endDate", event.target.value)
                      }
                    />
                  </div>
                </div>
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
                  <span>Кількість показів на день</span>
                  <input
                    type="number"
                    min="1"
                    max="100000"
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
                <PriceSelect
                  label="Тип продукції"
                  items={pricesByCategory.print_product || []}
                  value={selectedProduct?.code || ""}
                  onChange={(value) => updateField("productType", value)}
                />
                <label className="calculator-field">
                  <span>Кількість</span>
                  <input
                    type="number"
                    min="1"
                    max="1000000"
                    value={form.printQuantity}
                    onChange={(event) =>
                      updateField("printQuantity", Number(event.target.value))
                    }
                  />
                </label>
                <PriceSelect
                  label="Матеріал"
                  items={pricesByCategory.print_material || []}
                  value={selectedMaterial?.code || ""}
                  onChange={(value) => updateField("materialCode", value)}
                />
                <PriceSelect
                  label="Розмір"
                  items={pricesByCategory.print_size || []}
                  value={selectedSize?.code || ""}
                  onChange={(value) => updateField("sizeCode", value)}
                />
                <PriceSelect
                  label="Кольоровість"
                  items={pricesByCategory.print_color || []}
                  value={selectedColor?.code || ""}
                  onChange={(value) => updateField("colorMode", value)}
                />
              </>
            )}

            <div className="calculator-days-row">
              <span>{currentType === "print" ? "Формат" : "Кількість днів"}</span>
              <strong>
                {currentType === "print"
                  ? selectedSize?.label || "—"
                  : `${days} днів`}
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
              <span>Орієнтовна вартість</span>
              <strong>{formatMoney(calculation.total)}</strong>
            </div>

            <button
              className="calculator-submit"
              type="submit"
              disabled={!calculation.ready}
            >
              Замовити прорахунок
              <span>→</span>
            </button>

            <p className="calculator-security">
              Остаточну суму перерахує менеджер за актуальними цінами БД
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
                  ? `${selectedProduct?.label || "—"}, ${form.printQuantity} шт.`
                  : selectedSpace?.location || "Оберіть рекламну площину"}
              </h2>
              <div className="preview-tags">
                {currentType === "billboard" && selectedSpace && (
                  <>
                    <span>Розмір: {selectedSpace.size || "—"}</span>
                    <span>
                      {form.startDate} — {form.endDate} ({days} днів)
                    </span>
                    <span>
                      Друк плаката: {form.needPosterPrint ? "так" : "ні"}
                    </span>
                  </>
                )}
                {currentType === "led" && selectedSpace && (
                  <>
                    <span>Розмір: {selectedSpace.size || "—"}</span>
                    <span>Тривалість: {form.videoDuration} сек</span>
                    <span>Показів на день: {form.showCount}</span>
                    <span>
                      {form.startDate} — {form.endDate} ({days} днів)
                    </span>
                  </>
                )}
                {currentType === "print" && (
                  <>
                    <span>Матеріал: {selectedMaterial?.label || "—"}</span>
                    <span>Розмір: {selectedSize?.label || "—"}</span>
                    <span>Колір: {selectedColor?.label || "—"}</span>
                  </>
                )}
              </div>
              <p className="preview-note">
                Параметри цього калькулятора будуть передані менеджеру разом із
                заявкою та не змішуватимуться з іншими типами послуг.
              </p>
            </div>
          </aside>
        </section>
      </main>
    </div>
  );
}

function PriceSelect({ label, items, value, onChange }) {
  return (
    <label className="calculator-field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {items.map((item) => (
          <option key={item.code} value={item.code}>
            {item.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export default CalculatorPage;
