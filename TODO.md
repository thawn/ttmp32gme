* import/migrate library from one computer to another - can already be done manually, needs documentation. GUI for this will not be done.
* test docker image and create a pre-release v2.0.0_rc1
* port MacOS deployment to python (automate in CI)
* PDF generation: create reproducible working PDFs irrespective of the browser that the user is using. The PDF generation needs a browser engine that runs headless and supports JavaScript. make sure the PDFs created by the browser version used work for OID printing (ideally PNG images are not changed in the PDF)
  * selenium + browser is a good option because it allows us to try several different browsers we can first check with a live browser if the PDFs generate working codes. also, we already use sodium for the end-to-end tests so the additional packaging overhead is minimal
  * if selenium and browsers fail, try [playwright] (https://www.checklyhq.com/docs/learn/playwright/generating-pdfs/)
  * wkhtml2pdf works for Windows but development is stale and PDFs only work in a very old version with known vulnerabilities
* port Windows deployment to python (automate in CI)
* save last selected albums in the browsers local storage
