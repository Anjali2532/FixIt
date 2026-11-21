import { test, expect } from "@playwright/test";
import path from "node:path";

const email = process.env.FIXIT_E2E_EMAIL;
const password = process.env.FIXIT_E2E_PASSWORD;
if (!email || !password) {
  throw new Error(
    "Set FIXIT_E2E_EMAIL and FIXIT_E2E_PASSWORD for the separate 100-report demo database.",
  );
}

async function login(page, user = email) {
  await page.goto("/login");
  await page.getByLabel("Email address", { exact: true }).fill(user);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Log In", exact: true }).click();
  await expect(page).toHaveURL(
    user.includes("resident") ? /my-reports/ : /admin\/dashboard/,
  );
  await expect(page.getByRole("table")).toBeVisible();
}

async function waitForList(page, action) {
  const response = page.waitForResponse((result) => {
    const url = new URL(result.url());
    return (
      url.pathname === "/api/issues" && result.request().method() === "GET"
    );
  });
  await action();
  expect((await response).status()).toBe(200);
  await expect(page.getByRole("table")).toBeVisible();
}

async function screenshot(page, filename) {
  if (process.env.FIXIT_SCREENSHOTS) {
    await page.screenshot({
      path: path.join(process.env.FIXIT_SCREENSHOTS, filename),
    });
  }
}

test.beforeEach(async ({ page }) => {
  await login(page);
});

test("filtered page and order survive refresh", async ({ page }) => {
  await waitForList(page, () =>
    page.getByLabel("Status", { exact: true }).selectOption("Reported"),
  );
  await waitForList(page, () =>
    page.getByLabel("Sort reports").selectOption("oldest"),
  );
  await waitForList(page, () =>
    page.getByRole("button", { name: "Next", exact: true }).click(),
  );
  await expect(page.getByText("Page 2 of 2", { exact: true })).toBeVisible();
  const rows = await page
    .locator("tbody tr td:first-child a")
    .allTextContents();
  await page.reload();
  await expect(page.getByRole("table")).toBeVisible();
  await expect(page.getByLabel("Status", { exact: true })).toHaveValue(
    "Reported",
  );
  await expect(page.getByLabel("Sort reports")).toHaveValue("oldest");
  await expect(page.getByText("Page 2 of 2", { exact: true })).toBeVisible();
  expect(
    await page.locator("tbody tr td:first-child a").allTextContents(),
  ).toEqual(rows);
  expect(new URL(page.url()).searchParams.get("page")).toBe("2");
  await page.setViewportSize({ width: 1280, height: 1500 });
  await screenshot(page, "week5-filter-restoration.png");
});

test("column buttons toggle both sort directions", async ({ page }) => {
  for (const [label, column] of [
    ["Category", 2],
    ["Status", 7],
  ]) {
    for (const direction of ["ascending", "descending"]) {
      await waitForList(page, () =>
        page
          .getByRole("button", {
            name: `Sort by ${label.toLowerCase()}`,
            exact: true,
          })
          .click(),
      );
      await expect(
        page.getByRole("columnheader").filter({
          has: page.getByRole("button", {
            name: `Sort by ${label.toLowerCase()}`,
            exact: true,
          }),
        }),
      ).toHaveAttribute("aria-sort", direction);
      const values = await page
        .locator(`tbody tr td:nth-child(${column})`)
        .allTextContents();
      const ordered = [...values].sort();
      if (direction === "descending") ordered.reverse();
      expect(values).toEqual(ordered);
    }
  }
  await screenshot(page, "week5-dashboard-sorting.png");
});

test("back navigation restores filters and changing a filter resets the page", async ({
  page,
}) => {
  await page.goto("/admin/dashboard?status=Reported&sort=oldest&page=2");
  await expect(page.getByText("Page 2 of 2", { exact: true })).toBeVisible();
  await waitForList(page, () =>
    page.getByLabel("Status", { exact: true }).selectOption("In Progress"),
  );
  expect(new URL(page.url()).searchParams.has("page")).toBe(false);
  await page.goBack();
  await expect(page.getByText("Page 2 of 2", { exact: true })).toBeVisible();
  await expect(page.getByLabel("Status", { exact: true })).toHaveValue(
    "Reported",
  );
});

test("a shared filter URL works and clear filters restores all reports", async ({
  page,
}) => {
  await page.goto("/admin/dashboard?assignee=999999&sort=category-desc");
  await expect(
    page.getByRole("heading", { name: "No matching reports" }),
  ).toBeVisible();
  await expect(
    page.getByText("Try different filters or clear them to see more reports."),
  ).toBeVisible();
  await waitForList(page, () =>
    page.getByRole("button", { name: "Clear filters", exact: true }).click(),
  );
  expect(new URL(page.url()).search).toBe("");
  await expect(
    page.getByText("Showing 100 of 100 reports", { exact: true }),
  ).toBeVisible();
});

test("mobile filters restore without horizontal page overflow", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/admin/dashboard?category=Lighting&sort=category-desc");
  await expect(page.locator(".report-list")).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Category", { exact: true })).toHaveValue(
    "Lighting",
  );
  await expect(page.getByLabel("Sort reports")).toHaveValue("category-desc");
  await expect(page.locator(".report-list")).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page
    .locator(".report-filters")
    .evaluate((element) => element.scrollIntoView({ block: "start" }));
  await screenshot(page, "week5-mobile-filters.png");
});

test("resident sorting and shared URLs do not reveal other residents reports", async ({
  page,
}) => {
  await page.getByRole("button", { name: "Log Out", exact: true }).click();
  await login(page, "demo.resident1@example.test");
  await page.goto("/my-reports?sort=status-desc");
  await expect(
    page.getByText("Showing 34 of 34 reports", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("columnheader", { name: "Reported by", exact: true }),
  ).toHaveCount(0);
  const response = await page.request.get("/api/issues?sort=status-desc");
  expect(response.status()).toBe(200);
  expect((await response.json()).total_all).toBe(34);
});
