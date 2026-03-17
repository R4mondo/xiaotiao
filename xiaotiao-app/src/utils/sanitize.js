/**
 * XSS Sanitization Utility
 * Escapes special HTML characters to prevent injection attacks
 * when rendering LLM-generated content via innerHTML.
 */

const ESCAPE_MAP = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#x27;',
};

const ESCAPE_RE = /[&<>"']/g;

/**
 * Escape a string for safe insertion into HTML.
 * @param {string} str - Raw string (e.g. from LLM response)
 * @returns {string} Escaped string safe for innerHTML
 */
export function escapeHtml(str) {
  if (typeof str !== 'string') return '';
  return str.replace(ESCAPE_RE, (ch) => ESCAPE_MAP[ch]);
}

/**
 * Sanitize HTML output – allows only safe tags (<p>, <br>, <strong>, <em>, <ul>, <ol>, <li>)
 * and strips everything else. Intended for LLM-generated article HTML.
 * @param {string} html - HTML string from LLM
 * @returns {string} Sanitized HTML
 */
export function sanitizeHtml(html) {
  if (typeof html !== 'string') return '';
  // Allow only whitelisted tags
  const ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'b', 'i', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre', 'span', 'div', 'a'];
  const ALLOWED_ATTRS = ['href', 'target', 'rel', 'class', 'style'];

  // Use DOMParser to safely parse
  const doc = new DOMParser().parseFromString(html, 'text/html');
  
  function cleanNode(node) {
    const children = Array.from(node.childNodes);
    children.forEach(child => {
      if (child.nodeType === Node.TEXT_NODE) return; // text is safe
      if (child.nodeType === Node.ELEMENT_NODE) {
        const tag = child.tagName.toLowerCase();
        if (tag === 'script' || tag === 'iframe' || tag === 'object' || tag === 'embed') {
          child.remove();
          return;
        }
        if (!ALLOWED_TAGS.includes(tag)) {
          // Replace with its children
          const parent = child.parentNode;
          while (child.firstChild) parent.insertBefore(child.firstChild, child);
          parent.removeChild(child);
          return;
        }
        // Remove dangerous attributes
        Array.from(child.attributes).forEach(attr => {
          const name = attr.name.toLowerCase();
          if (!ALLOWED_ATTRS.includes(name)) {
            child.removeAttribute(attr.name);
          }
          // Remove javascript: URIs
          if (name === 'href' && attr.value.trim().toLowerCase().startsWith('javascript:')) {
            child.removeAttribute('href');
          }
        });
        // Remove event handlers
        Array.from(child.attributes).forEach(attr => {
          if (attr.name.toLowerCase().startsWith('on')) {
            child.removeAttribute(attr.name);
          }
        });
        cleanNode(child);
      } else {
        child.remove();
      }
    });
  }

  cleanNode(doc.body);
  return doc.body.innerHTML;
}
