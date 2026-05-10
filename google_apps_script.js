// ═══════════════════════════════════════════════════════════════
//  WAREHOUSE LIGHT REPORT — Google Apps Script
//  Paste this entire file into script.google.com
//  Then: Deploy → New deployment → Web app
//        Execute as: Me  |  Who has access: Anyone
// ═══════════════════════════════════════════════════════════════

// ⚙️ Set this to the ID of your Google Sheet
// (the long string in the URL: docs.google.com/spreadsheets/d/THIS_PART/edit)
const SHEET_ID = 'YOUR_GOOGLE_SHEET_ID_HERE';

// Name of the tab inside the sheet where data will be written
const SHEET_TAB = 'Reports';

// Column headers — must match the payload keys sent from the HTML form
const HEADERS = [
  'Timestamp',
  'Zone',
  'Light_ID',
  'Issue',
  'Action',
  'Cost_PKR',
  'Name',
  'Role',
  'Notes'
];

// ─────────────────────────────────────────────────────────────
//  doPost — receives POST request from the HTML form
// ─────────────────────────────────────────────────────────────
function doPost(e) {
  try {
    const ss    = SpreadsheetApp.openById(SHEET_ID);
    let   sheet = ss.getSheetByName(SHEET_TAB);

    // Create the tab + headers if it doesn't exist yet
    if (!sheet) {
      sheet = ss.insertSheet(SHEET_TAB);
      sheet.appendRow(HEADERS);
      sheet.getRange(1, 1, 1, HEADERS.length)
           .setFontWeight('bold')
           .setBackground('#1C4ED8')
           .setFontColor('#FFFFFF');
      sheet.setFrozenRows(1);
    }

    // Parse the incoming JSON
    const data = JSON.parse(e.postData.contents);

    // Build a row in header order
    const row = HEADERS.map(h => data[h] !== undefined ? data[h] : '');
    sheet.appendRow(row);

    // Auto-resize columns for readability
    sheet.autoResizeColumns(1, HEADERS.length);

    return ContentService
      .createTextOutput(JSON.stringify({ status: 'ok' }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ status: 'error', message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// ─────────────────────────────────────────────────────────────
//  doGet — health check (visit the web app URL in browser)
// ─────────────────────────────────────────────────────────────
function doGet(e) {
  return ContentService
    .createTextOutput('✅ Light Report Script is running.')
    .setMimeType(ContentService.MimeType.TEXT);
}
