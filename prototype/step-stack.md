# Step three - the stack (build-less, single page)

Default to one HTML file that runs by double-clicking. **No build step, no Babel, ever.**

Use **htm** - JSX-like markup expressed as tagged template literals, bound to `React.createElement`. No transpile pass, no `<script type="text/babel">`, no XHR for source files. The prototype opens by double-clicking `index.html` *and* runs identically when served over HTTP.


```
index.html              CDN scripts (React UMD + htm), loads app.js as a plain <script>
data.js                 window.DEMO blob - all mock data lives here
styles.css              Token block at top + every class for the screen
*.js                    Components grouped by visual region (or one app.js for small)
```



`index.html` template:


```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=1440"/>
  <title>{{Project name}}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={{Sans}}:wght@400;500;600;700&family={{Secondary}}&display=swap"/>
  <link rel="stylesheet" href="styles.css"/>
</head>
<body>
  <div id="root"></div>
  <script src="https://unpkg.com/react@18.3.1/umd/react.development.js"></script>
  <script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js"></script>
  <script src="https://unpkg.com/htm@3.1.1/dist/htm.umd.js"></script>
  <script src="data.js"></script>
  <script src="app.js"></script>
</body>
</html>
```


`app.js` header - bind htm once, then write JSX-like trees inside `html` tagged templates:


```js
const { useState, useEffect, useRef, useMemo } = React;
const { createRoot } = ReactDOM;
const h = React.createElement;
const html = htm.bind(h);

function App() {
  return html`<div className="app">Hello ${name}</div>`;
}

createRoot(document.getElementById("root")).render(html`<${App}/>`);
```


**htm vs JSX - the only syntax differences:**

| JSX | htm |
|---|---|
| `<Comp prop={x}>` | `<${Comp} prop=${x}>` |
| `</Comp>` | `<//>` (or `</${Comp}>`) |
| `{value}` (children or attr) | `${value}` |
| `{...spread}` | `...${spread}` |
| `style={{ color: "red" }}` | `style=${{ color: "red" }}` |
| `dangerouslySetInnerHTML={{__html:s}}` | `dangerouslySetInnerHTML=${{__html:s}}` |
| `<>...</>` (fragment) | `<${React.Fragment}>...<//>` |

Everything else - `className`, event handlers, refs, `key`, conditional `&&`, `.map`, SVG, iframes, hooks - is identical.

For pure HTML/CSS prototypes (static editorial, marketing, brutalist), skip React/htm entirely.
