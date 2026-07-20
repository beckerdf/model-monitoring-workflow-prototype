# Model Monitoring Review Assignment — Workflow Prototype

Sandbox repo for prototyping the automated model monitoring review assignment
workflow before it's built out in a real TFS repository.

## What's here

- **`/prototype`** — click-through React prototype simulating the full workflow
  (governance inbox → auto-parse → auto-assign → notify → track → escalate).
  Built as a Claude artifact; drop `App.jsx` into any React sandbox (e.g.
  CodeSandbox, Vite) to run it locally.
- **`/docs`** — the full workflow write-up (current state, proposed state,
  architecture) and the summary deck used for the national manager walkthrough.
- **`/schema`** — field-level schema for the two SharePoint lists this design
  depends on: the Rotation Queue and the Review Inventory.
- **`.github/workflows/ci.yml`** — validates the repo structure on every push;
  placeholder for the CI/CD pipeline this becomes once real code (Power Automate
  exports, parsing logic, etc.) lives here.

## Status

Prototype / proposal stage. Not connected to any live TFS system — this is a
sandbox to test the design and demo it before standing up the real repo and
production workflow.

## Next up

- Data flow detail: exactly how the Archer-generated email is parsed, what's
  captured, and how it's stored (to be added as the design gets tested)
- Visuals for the data flow, once finalized
- Migration plan to the real TFS repo once the design is signed off
