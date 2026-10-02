// D768 fixture parser: USDA FAS daily export-sales announcements -> one row per sale clause.
//
// HOW THE INPUT WAS COLLECTED (2026-10-02). The site answers non-browser clients with 403 and this repo does not
// spoof clients, so everything ran in a browser on https://www.fas.usda.gov:
//   1. The listing pages 24-101 of /newsroom/search?news[0]=news_programs:17 (12 cards each), fetched one at a time,
//      retried after any 403. Each card was read as {d: listing date, href, title, tx: whitespace-collapsed text}
//      and kept when the listing year is 2016-2023: 920 cards, 0 duplicate hrefs, dates monotone across pages.
//      Cards dated 2024 or later were dropped unread.
//   2. A card's listing text is cut at about 250 characters. Where the cut could hide a sale (the first sentence
//      unfinished, or nothing parsed) and for every cancellation, correction and retraction, the announcement's own
//      page was fetched (210 pages) and its <main article> text used instead (FULL[href]).
// parseCard() below is the exact code that produced data/fixtures/usda_daily_export_sales.csv. Every row carries its
// announcement's path, so any row can be checked at https://www.fas.usda.gov/newsroom/<slug>.
//
// Columns: date (listing date = the release date; the release is 09:00 ET), slug, title_kind (announcement |
// correction | retraction | cancellation | notice), kind (sale | cancel | change | restated | none; "restated" is a
// clause that re-states an earlier announcement inside a correction, never a new sale), tonnes, commodity
// (normalised), destination (as written; "unknown destinations" kept), my (marketing year where stated), source
// (full | listing), status (ok | unparsed), dateline (match | mismatch | none: the "WASHINGTON, <date>" dateline
// against the listing date), dateline_date (the dateline as written, parsed; typos such as a wrong year are kept).

const MONTHS = {January: 1, February: 2, March: 3, April: 4, May: 5, June: 6, July: 7, August: 8, September: 9,
  October: 10, November: 11, December: 12};
const MON3 = {Jan: 1, Feb: 2, Mar: 3, Apr: 4, May: 5, Jun: 6, June: 6, Jul: 7, July: 7, Aug: 8, Sep: 9, Sept: 9,
  Oct: 10, Nov: 11, Dec: 12, March: 3, April: 4};

function isoDate(d) {
  const m = d.match(/^(\w+) (\d{1,2}), (\d{4})$/);
  return `${m[3]}-${String(MONTHS[m[1]]).padStart(2, "0")}-${m[2].padStart(2, "0")}`;
}

function datelineOf(text) {
  const m = text.match(/WASHINGTON,? (\w+)\.? (\d{1,2}),? (\d{4})/);
  if (!m) return "";
  const mo = MON3[m[1]] || MONTHS[m[1]];
  return mo ? `${m[3]}-${String(mo).padStart(2, "0")}-${m[2].padStart(2, "0")}` : "";
}

function normCommodity(c) {
  c = (c || "").toLowerCase().replace(/\s+/g, " ").trim();
  if (/soybean (cake and )?meal|soybean cake/.test(c)) return "soybean_meal";
  if (/soybean oil/.test(c)) return "soybean_oil";
  if (/soybean/.test(c)) return "soybeans";
  if (/corn/.test(c)) return "corn";
  if (/wheat|durum/.test(c)) return "wheat";
  if (/sorghum/.test(c)) return "sorghum";
  if (/barley/.test(c)) return "barley";
  if (/oats/.test(c)) return "oats";
  return c ? "other:" + c : "";
}

function titleKind(t) {
  if (/Statement|Notice of|Schedule Change|Keeps U\.S\.|Clarifies|Updates Schedule|Error in|Report Delayed/i.test(t)) return "notice";
  if (/retraction/i.test(t)) return "retraction";
  if (/correct/i.test(t)) return "correction";
  if (/cancell?ation/i.test(t)) return "cancellation";
  return "announcement";
}

// The body runs from the dateline (or the first "Private exporters" when there is none) to the first boilerplate:
// the marketing-year note, the reporting-rule paragraph, the ### footer, or the page's "Related News" block (which
// lists the site's LATEST announcements and must never be parsed).
const CUT = /###|The U\.S\. Department of Agriculture is required|The marketing years? for|USDA issues both daily|Exporters are required|For further information|Related News/;

function bodyOf(card, FULL) {
  const full = FULL[card.href];
  // the page's own text ends at the first boilerplate; search for the body's start only before it, so a page whose
  // body has neither marker (the 2022-07-15 retraction) is never re-anchored inside the "Related News" block
  let t = (full || card.tx).split(CUT)[0];
  const w = t.search(/WASHINGTON/);
  const i = w >= 0 ? w : t.search(/Private exporters/);
  if (i >= 0) t = t.slice(i);
  return {text: t, source: full ? "full" : "listing"};
}

// An announcement that corrects an earlier one restates it: everything before "The corrected announcement is as
// follows:" refers to the old announcement, and the first sentence after it is the corrected restatement. Only the
// clauses after that sentence are new sales.
function restatedEnd(s) {
  const k = s.search(/corrected announcement is as follows:/i);
  if (k < 0) return 0;
  const after = s.slice(k);
  const dot = after.search(/marketing year\.|\.\s/);
  return k + (dot >= 0 ? dot + 1 : after.length);
}

function tonnesOf(num, k) {
  const v = parseFloat(num.replace(/,/g, ""));
  return k ? Math.round(v * 1000) : Math.round(v);
}

function parseCard(card, FULL) {
  const date = isoDate(card.d);
  const slug = card.href.replace(/^\/newsroom\//, "");
  const tk = titleKind(card.title);
  const {text, source} = bodyOf(card, FULL);
  const dl = datelineOf(text);
  const base = {date, slug, title_kind: tk, source, dateline: !dl ? "none" : dl === date ? "match" : "mismatch", dateline_date: dl};
  if (tk === "notice") return [{...base, kind: "none", tonnes: "", commodity: "", destination: "", my: "", status: "ok"}];
  const s = text;
  const myAll = (s.match(/(\d{4}\/\d{2,4})/) || [])[1] || "";
  const rEnd = restatedEnd(s);
  const kindOf = (idx, before) => {
    if (tk === "correction" || tk === "retraction" || idx < rEnd) return "restated";
    if (tk === "cancellation" || /cancel/i.test(before)) return "cancel";
    return "sale";
  };
  const rows = [];
  if (/changes? in destination of/i.test(s) && rEnd === 0) {
    const m = s.match(/([\d,.]+)\s?(K)?\s?(?:metric tons|MT|tons) of ([a-z][a-z ]*?) from (.+?) to (?:the )?([A-Z][A-Za-z'-]*(?: [A-Z][A-Za-z'-]*)*)/);
    rows.push({...base, kind: "change", tonnes: m ? tonnesOf(m[1], m[2]) : "", commodity: m ? normCommodity(m[3]) : "",
      destination: m ? m[5].trim() : "", my: myAll, status: m ? "ok" : "unparsed"});
    return rows;
  }
  const re = /([\d,.]+)\s?(K)?\s?(?:metric tons|MT|tons)(?: of ([a-z][a-z ,]*?))?(?: for delivery| received during the reporting period for delivery)? to (?:the )?(unknown destinations?|[A-Z][A-Za-z'-]*(?: [A-Z][A-Za-z'-]*)*)/g;
  // "reported soybean sales of 198,000 MT for delivery to China ...": the commodity before "sales"
  let m, last = ((s.match(/reported (?:to [A-Za-z.' ]+? )?([a-z][a-z ]*?) sales of/) || [])[1] || "").trim();
  const dest = d => /^unknown destination/.test(d) ? "unknown destinations" : d.trim();
  while ((m = re.exec(s)) !== null) {
    const com = m[3] ? m[3].replace(/,$/, "").trim() : last;
    if (m[3]) last = com;
    const before = s.slice(Math.max(0, m.index - 80), m.index);
    const tail = s.slice(m.index, m.index + m[0].length + 70);
    const my = (tail.match(/(\d{4}\/\d{2,4})/) || [])[1] || myAll;
    rows.push({...base, kind: kindOf(m.index, before), tonnes: tonnesOf(m[1], m[2]), commodity: normCommodity(com),
      destination: dest(m[4]), my, status: "ok"});
  }
  if (rows.length === 0) {
    // "sales to China: 330,000 MT of soybeans - 66,000 MT ... and 204,000 MT of soybeans received ..." (destination first)
    const h = s.match(/(?:sales?|activity) (?:to|for) (?:the )?(unknown destinations?|[A-Z][A-Za-z'-]*(?: [A-Z][A-Za-z'-]*)*):/);
    if (h) {
      const re2 = /([\d,.]+)\s?(K)?\s?(?:metric tons|MT|tons) of ([a-z][a-z ]*?)(?= -| –|,| for| during| received|\.|;| and)/g;
      while ((m = re2.exec(s)) !== null) {
        const before = s.slice(Math.max(0, m.index - 80), m.index);
        rows.push({...base, kind: kindOf(m.index, before), tonnes: tonnesOf(m[1], m[2]), commodity: normCommodity(m[3]),
          destination: dest(h[1]), my: myAll, status: "ok"});
      }
    }
  }
  if (rows.length === 0) rows.push({...base, kind: "none", tonnes: "", commodity: "", destination: "", my: myAll, status: "unparsed"});
  return rows;
}

const COLS = ["date", "slug", "title_kind", "kind", "tonnes", "commodity", "destination", "my", "source", "status", "dateline",
  "dateline_date"];

function toCsv(rows) {
  const q = v => /[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v);
  return [COLS.join(",")].concat(rows.map(r => COLS.map(c => q(r[c])).join(","))).join("\n") + "\n";
}

// in the page: window.__rows = window.__keep.flatMap(c => parseCard(c, window.__full)); toCsv(window.__rows)
