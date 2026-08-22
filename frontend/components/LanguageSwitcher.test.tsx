import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { LocaleProvider } from "@/lib/i18n/LocaleProvider";

describe("LanguageSwitcher", () => {
  it("switches the active locale when a language button is clicked", async () => {
    const user = userEvent.setup();

    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );

    const ruButton = screen.getByRole("button", { name: "RU" });
    const enButton = screen.getByRole("button", { name: "EN" });

    expect(enButton).toHaveAttribute("aria-pressed", "true");
    expect(ruButton).toHaveAttribute("aria-pressed", "false");

    await user.click(ruButton);

    expect(ruButton).toHaveAttribute("aria-pressed", "true");
    expect(enButton).toHaveAttribute("aria-pressed", "false");
    expect(localStorage.getItem("rexab_locale")).toBe("ru");
  });
});
