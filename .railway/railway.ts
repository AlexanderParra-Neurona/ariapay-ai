import { defineRailway, project, service } from "railway/iac";

// Last resort for a per-service CaC repo. Prefer one .railway file for the
// project and drop this if you later combine services into that file.
export const partial = "ariabot";

export default defineRailway(() => {
  const ariabot = service("ariabot", {
    healthcheck: "/v1/health",
    healthcheckTimeout: 30,
    // dockerfilePath from CaC: "Dockerfile"
    // builder from CaC: "DOCKERFILE"
  });
  return project("ariapay-ai", {
    resources: [ariabot],
  });
});
