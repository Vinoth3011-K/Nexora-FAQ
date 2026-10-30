import { FAQS_DATA, FAQ_CATEGORIES } from './src/data/faqs.js';
import { 
  fetchHealth, 
  fetchFAQs, 
  fetchFAQCategories, 
  searchFAQs, 
  sendChatMessage, 
  fetchConversations, 
  fetchConversation, 
  createConversation, 
  clearConversation 
} from './src/services/api.js';
import { createNewConversation } from './src/utils/storage.js';
import fs from 'fs';
import path from 'path';

console.log('=== TEST SUITE: RAG COMPANY FAQ CHATBOT FRONTEND ===\n');

let passedTests = 0;
let totalTests = 0;

function assert(condition, testName) {
  totalTests++;
  if (condition) {
    console.log(`[PASS] ${testName}`);
    passedTests++;
  } else {
    console.error(`[FAIL] ${testName}`);
  }
}

// 1. FAQ Data Validation
console.log('--- 1. FAQ Data Validation ---');
assert(FAQS_DATA.length >= 12, `FAQ dataset contains at least 12 FAQs (actual: ${FAQS_DATA.length})`);
assert(FAQ_CATEGORIES.length === 6, `Categories include All + 5 distinct categories (actual: ${FAQ_CATEGORIES.length})`);

const requiredCategories = [
  'General Information',
  'Products & Services',
  'Pricing & Payments',
  'Refunds & Cancellations',
  'Customer Support'
];

for (const cat of requiredCategories) {
  const count = FAQS_DATA.filter(f => f.category === cat).length;
  assert(count > 0, `Category "${cat}" has sample data (${count} entries)`);
}

const allHaveFields = FAQS_DATA.every(f => f.id && f.category && f.question && f.answer && Array.isArray(f.keywords) && f.keywords.length > 0);
assert(allHaveFields, 'All FAQs contain id, category, question, answer, and keywords array');

// 2. Real API Service Client Validation
console.log('\n--- 2. Real API Service Client Validation ---');
assert(typeof sendChatMessage === 'function', 'sendChatMessage is exported as a function');
assert(typeof fetchHealth === 'function', 'fetchHealth is exported as a function');
assert(typeof fetchFAQs === 'function', 'fetchFAQs is exported as a function');
assert(typeof fetchFAQCategories === 'function', 'fetchFAQCategories is exported as a function');
assert(typeof searchFAQs === 'function', 'searchFAQs is exported as a function');
assert(typeof fetchConversations === 'function', 'fetchConversations is exported as a function');
assert(typeof fetchConversation === 'function', 'fetchConversation is exported as a function');
assert(typeof createConversation === 'function', 'createConversation is exported as a function');
assert(typeof clearConversation === 'function', 'clearConversation is exported as a function');

try {
  const health = await fetchHealth();
  assert(health.status === 'healthy', `Backend API health endpoint responded healthy (${health.service})`);
} catch (err) {
  console.warn('[Warning] Backend live health test skipped or unreachable:', err.message);
}

// 3. Conversation Management Validation
console.log('\n--- 3. Conversation Management Validation ---');
const conv1 = createNewConversation('Custom Title');
assert(conv1.id.startsWith('conv_'), 'Created conversation has unique ID with conv_ prefix');
assert(conv1.title === 'Custom Title', 'Created conversation retains custom title');
assert(Array.isArray(conv1.messages) && conv1.messages.length === 0, 'Created conversation has empty messages array');

// 4. CSS Architecture & Code Rules Verification
console.log('\n--- 4. CSS Architecture & Rule Verification ---');

const srcDir = fs.existsSync('./src') ? './src' : (fs.existsSync('./frontend/src') ? './frontend/src' : path.join(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([a-zA-Z]:)/, '$1')), 'src'));

function scanDir(dir, filterFn) {
  let results = [];
  const list = fs.readdirSync(dir);
  for (const file of list) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      results = results.concat(scanDir(fullPath, filterFn));
    } else if (filterFn(file)) {
      results.push(fullPath);
    }
  }
  return results;
}

// Check CSS files: ONLY src/index.css must exist
const cssFiles = scanDir(srcDir, f => f.endsWith('.css'));
assert(cssFiles.length === 1 && cssFiles[0].replace(/\\/g, '/').endsWith('src/index.css'), `Strict CSS check: Only src/index.css exists (found: ${cssFiles.join(', ')})`);

// Check JSX files for inline styles: no style={{...}}
const jsxFiles = scanDir(srcDir, f => f.endsWith('.jsx'));
let hasInlineStyle = false;
let hasTailwindClass = false;

const tailwindPatterns = ['bg-blue-', 'text-red-', 'flex-row', 'p-4', 'mt-2', 'rounded-lg', 'shadow-md', 'grid-cols-'];

for (const jsxPath of jsxFiles) {
  const content = fs.readFileSync(jsxPath, 'utf8');
  if (/style\s*=\s*\{\{/.test(content)) {
    console.error(`Found inline style in ${jsxPath}`);
    hasInlineStyle = true;
  }
  for (const tw of tailwindPatterns) {
    if (new RegExp(`className=["'][^"']*\\b${tw}`).test(content)) {
      console.error(`Found potential Tailwind class ${tw} in ${jsxPath}`);
      hasTailwindClass = true;
    }
  }
}

assert(!hasInlineStyle, 'No inline style={{...}} props found in any JSX file');
assert(!hasTailwindClass, 'No Tailwind utility classes found in JSX files');

// 5. Check HTTP Server
console.log('\n--- 5. Dev Server Verification ---');
try {
  const response = await fetch('http://localhost:3000/');
  const html = await response.text();
  assert(response.status === 200, `Dev server responded with HTTP 200 (actual: ${response.status})`);
  assert(html.includes('<title>Nexora FAQ Assistant'), 'HTML contains correct title');
  assert(html.includes('/src/main.jsx'), 'HTML entry point is /src/main.jsx');
} catch (e) {
  console.error('Failed to fetch from dev server:', e.message);
  assert(false, 'Dev server is accessible at http://localhost:3000/');
}

console.log(`\n=============================================`);
console.log(`FINAL RESULT: ${passedTests} / ${totalTests} TESTS PASSED`);
console.log(`=============================================\n`);
