import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LocaleProvider, useTranslation } from "@/lib/i18n/LocaleProvider";

function TestConsumer() {
  const { locale, setLocale, t } = useTranslation();
  return (
    <div>
      <p>locale: {locale}</p>
      <p>{t("common.cancel")}</p>
      <button onClick={() => setLocale("ru")}>switch to ru</button>
    </div>
  );
}

function MissingKeyConsumer() {
  const { t } = useTranslation();
  return <p>{t("nonexistent.key")}</p>;
}

function setBrowserLanguage(language: string) {
  Object.defineProperty(window.navigator, "language", {
    value: language,
    configurable: true,
  });
}

describe("LocaleProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    setBrowserLanguage("en-US");
  });

  it("detects Russian from the browser language when nothing is stored", () => {
    setBrowserLanguage("ru-RU");

    render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );

    expect(screen.getByText("locale: ru")).toBeInTheDocument();
    expect(screen.getByText("Отмена")).toBeInTheDocument();
  });

  it("defaults to English for a non-Russian browser language", () => {
    setBrowserLanguage("fr-FR");

    render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );

    expect(screen.getByText("locale: en")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("prefers a stored locale over the browser language", () => {
    localStorage.setItem("rexab_locale", "ru");
    setBrowserLanguage("en-US");

    render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );

    expect(screen.getByText("locale: ru")).toBeInTheDocument();
  });

  it("persists a manual locale switch and re-renders with new translations", async () => {
    const user = userEvent.setup();

    render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );

    expect(screen.getByText("locale: en")).toBeInTheDocument();

    await user.click(screen.getByText("switch to ru"));

    expect(screen.getByText("locale: ru")).toBeInTheDocument();
    expect(screen.getByText("Отмена")).toBeInTheDocument();
    expect(localStorage.getItem("rexab_locale")).toBe("ru");
  });

  it("falls back to the key itself for a missing translation", () => {
    render(
      <LocaleProvider>
        <MissingKeyConsumer />
      </LocaleProvider>,
    );

    expect(screen.getByText("nonexistent.key")).toBeInTheDocument();
  });

  it("throws when used outside a LocaleProvider", () => {
    function Bare() {
      useTranslation();
      return null;
    }
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});

    expect(() => render(<Bare />)).toThrow(
      "useTranslation must be used within a LocaleProvider",
    );

    spy.mockRestore();
  });
});
