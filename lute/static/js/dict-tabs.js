"use strict";


/**
 * A general lookup button, for images, sentences, etc.
 */
class LookupButton {

  /** State required by the buttons. */
  static TERM_FORM_CONTAINER = null;
  static TERM_DICTS = null;
  static LANG_ID = null;


  /** All LookupButtons created. */
  static all = [];

  constructor(frameName) {
    let createIFrame = function(name) {
      const f = document.createElement("iframe");
      f.name = name;
      f.src = "about:blank";
      f.classList.add("dictframe");
      return f;
    };

    this.dictID = null;
    this.is_active = false;
    this.contentLoaded = false;

    this.frame = createIFrame(frameName);
    this.btn = document.createElement("button");
    this.btn.classList.add("dict-btn");
    this.btn.onclick = () => this.do_lookup();

    LookupButton.all.push(this);
  }

  /** Lookup. *************************/

  do_lookup() {
    throw new Error('Subclasses must override.');
  }

  /** Activate/deact. *************************/

  deactivate() {
    this.is_active = false;
    this.btn.classList.remove("dict-btn-active");
    this.frame.classList.remove("dict-active");
  }

  activate() {
    DictButton.all.forEach(button => button.deactivate());
    this.is_active = true;
    this.btn.classList.add("dict-btn-active");
    this.frame.classList.add("dict-active");
  }

};


/**
 * A general lookup button that's doesn't use dictionaries.
 * For buttons that get info about a term.
 * This content is never cached -- form values may change the search,
 * so it's fine to always reload.
 */
class GeneralLookupButton extends LookupButton {
  constructor(btn_id, btn_textContent, btn_title, btn_className, clickHandler) {
    super(`frame_for_${btn_id}`);

    const b = this.btn;
    b.setAttribute("id", btn_id);
    b.setAttribute("title", btn_title);
    b.textContent = btn_textContent;
    b.classList.add(btn_className);

    this.click_handler = clickHandler;
  }

  do_lookup() {
    this.click_handler(this.frame);
    this.activate();
  }

}  // end GeneralLookupButton


class SentenceLookupButton extends GeneralLookupButton {
  constructor() {
    let handler = function(iframe) {
      const txt = LookupButton.TERM_FORM_CONTAINER.querySelector("#text").value;
      // %E2%80%8B is the zero-width string.  The term is reparsed
      // on the server, so this doesn't need to be sent.
      const t = encodeURIComponent(txt).replaceAll('%E2%80%8B', '');
      const langid = `${LookupButton.LANG_ID ?? 0}`;
      if (langid == '0' || t == '')
        return;
      // Doing lookups by the term text (from the "#text" control) is
      // better than using a term ID, b/c it lets me search for new
      // multi-word terms in existing text, even before those
      // multi-word terms are actually created and saved.  e.g., I can
      // highlight the text "a big thing" and see if that phrase has
      // been used in anything I've read already.
      iframe.setAttribute("src", `/term/sentences/${LookupButton.LANG_ID}/${t}`);
    };

    super("sentences-btn", "Sentences", "See term usage", "dict-sentences-btn", handler);
  }
}


class ImageLookupButton extends GeneralLookupButton {
  constructor() {

    // Parents are in the tagify-managed #parentslist input box.
    let _get_parent_tag_values = function() {
      const pdata = LookupButton.TERM_FORM_CONTAINER.querySelector("#parentslist").value
      if ((pdata ?? '') == '')
        return [];
      return JSON.parse(pdata).map(e => e.value);
    };

    let handler = function(iframe) {
      const text = LookupButton.TERM_FORM_CONTAINER.querySelector("#text").value;
      const lang_id = LookupButton.LANG_ID;
      if (lang_id == null || lang_id == '' || parseInt(lang_id) == 0 || text == null || text == '') {
        alert('Please select a language and enter the term.');
        return;
      }
      let use_text = text;

      // If there is a single parent, use that as the basis of the lookup.
      const parents = _get_parent_tag_values();
      if (parents.length == 1)
        use_text = parents[0];

      const raw_bing_url = 'https://www.bing.com/images/search?q=[LUTE]&form=HDRSC2&first=1&tsc=ImageHoverTitle';
      const binghash = raw_bing_url.replace('https://www.bing.com/images/search?', '');
      const url = `/bing/search_page/${LookupButton.LANG_ID}/${encodeURIComponent(use_text)}/${encodeURIComponent(binghash)}`;

      iframe.setAttribute("src", url);
    };  // end handler

    super("dict-image-btn", null, "Lookup images", "dict-image-btn", handler);
  }
}


/**
 * AI Explanation button - calls the /api/explain endpoint.
 */
class AIExplainButton extends LookupButton {

  static isConfigured = null;  // null = not checked, true/false = status
  static explanationCache = new Map();  // Cache for explanations
  static currentText = null;  // Track current text being explained
  static currentTargetLanguage = null;  // Track current target language

  constructor() {
    super('ai-explain-frame');
    
    this.btn.textContent = '✨ AI Explain';
    this.btn.setAttribute("id", "ai-explain-btn");
    this.btn.setAttribute("title", "AI-powered explanation");
    this.btn.classList.add("dict-ai-explain-btn");
    
    // AI button should be treated like a dictionary button
    this.dictID = -1;  // Special ID for AI
  }

  do_lookup() {
    this.activate();
    
    if (LookupButton.TERM_FORM_CONTAINER == null) {
      this._show_error("Term form not loaded");
      return;
    }

    const text = LookupButton.TERM_FORM_CONTAINER.querySelector("#text").value;
    if (!text || text.trim() === '') {
      this._show_message("Please select some text to explain.");
      return;
    }

    // Check if AI is configured
    if (AIExplainButton.isConfigured === false) {
      this._show_not_configured_message();
      return;
    }

    // Store current text
    AIExplainButton.currentText = text;
    
    // Determine target language based on user preference
    const targetLang = this._get_target_language();
    AIExplainButton.currentTargetLanguage = targetLang;

    // Check cache first
    const cacheKey = this._get_cache_key(text, targetLang);
    if (AIExplainButton.explanationCache.has(cacheKey)) {
      console.log('Using cached AI explanation');
      this._render_markdown(AIExplainButton.explanationCache.get(cacheKey), targetLang);
      return;
    }

    // Make API call
    this._fetch_explanation(text, targetLang);
  }

  _get_cache_key(text, targetLanguage) {
    const lang_id = LookupButton.LANG_ID || 'unknown';
    return `${text}|${lang_id}|${targetLanguage}`;
  }

  _get_target_language() {
    // Check user preference - if they want to use target language (book's language)
    // or English as the explanation language
    const useTargetLanguage = LUTE_USER_SETTINGS.ai_explanation_use_target_language;
    
    if (useTargetLanguage && typeof LUTE_BOOK_LANGUAGE !== 'undefined' && LUTE_BOOK_LANGUAGE.name) {
      return LUTE_BOOK_LANGUAGE.name;
    }
    
    return 'English';
  }

  _get_language_name(lang_id) {
    // This is a simple mapping - ideally we'd get this from the server
    // For now, we'll pass the lang_id and let the backend handle it
    // The backend should accept language IDs or names
    return lang_id ? `Language_${lang_id}` : 'Unknown';
  }

  _fetch_explanation(text, targetLanguage) {
    this._show_streaming_loading();

    // Get language name from lang_id (we need this for the API)
    const lang_id = LookupButton.LANG_ID;
    
    // Try streaming first
    this._fetch_streaming_explanation(text, lang_id, targetLanguage);
  }

  _fetch_streaming_explanation(text, lang_id, targetLanguage) {
    let accumulatedText = '';
    
    fetch('/api/explain/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: text,
        source_language: this._get_language_name(lang_id),
        target_language: targetLanguage
      })
    })
    .then(async response => {
      if (!response.ok) {
        // If streaming fails, fall back to non-streaming
        console.log('Streaming failed, falling back to regular endpoint');
        this._fetch_regular_explanation(text, lang_id, targetLanguage);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        
        // Parse SSE events
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const eventData = JSON.parse(line.substring(6));
              
              if (eventData.chunk) {
                accumulatedText += eventData.chunk;
                // Show markdown text appearing in real-time
                this._update_streaming_display(accumulatedText);
              } else if (eventData.done) {
                // Streaming complete - show final markdown
                this._finalize_streaming(text, accumulatedText, targetLanguage);
                return;
              } else if (eventData.error) {
                throw new Error(eventData.error);
              }
            } catch (e) {
              // Ignore parsing errors for partial chunks
            }
          }
        }
      }

      // Stream ended without done event - show final result anyway
      this._finalize_streaming(text, accumulatedText, targetLanguage);
    })
    .catch(error => {
      console.error('Streaming error:', error);
      // Fall back to regular endpoint on error
      this._fetch_regular_explanation(text, lang_id, targetLanguage);
    });
  }

  _fetch_regular_explanation(text, lang_id, targetLanguage) {
    // Fallback to non-streaming markdown endpoint
    fetch('/api/explain/markdown', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: text,
        source_language: this._get_language_name(lang_id),
        target_language: targetLanguage
      })
    })
    .then(response => {
      if (!response.ok) {
        return response.json().then(err => {
          throw new Error(err.error || `HTTP ${response.status}`);
        });
      }
      return response.text();  // Get markdown text directly
    })
    .then(markdownText => {
      // Cache the result
      const cacheKey = this._get_cache_key(text, targetLanguage);
      AIExplainButton.explanationCache.set(cacheKey, markdownText);
      
      // Limit cache size to 50 entries
      if (AIExplainButton.explanationCache.size > 50) {
        const firstKey = AIExplainButton.explanationCache.keys().next().value;
        AIExplainButton.explanationCache.delete(firstKey);
      }
      
      // Render the markdown with toggle
      this._render_markdown(markdownText, targetLanguage);
    })
    .catch(error => {
      console.error('AI explanation error:', error);
      if (error.message.includes('not configured') || error.message.includes('500')) {
        AIExplainButton.isConfigured = false;
        this._show_not_configured_message();
      } else {
        this._show_error(`Error: ${error.message}`);
      }
    });
  }

  _finalize_streaming(text, accumulatedText, targetLanguage) {
    // Cache the markdown text
    const cacheKey = this._get_cache_key(text, targetLanguage);
    AIExplainButton.explanationCache.set(cacheKey, accumulatedText);
    
    // Limit cache size to 50 entries
    if (AIExplainButton.explanationCache.size > 50) {
      const firstKey = AIExplainButton.explanationCache.keys().next().value;
      AIExplainButton.explanationCache.delete(firstKey);
    }
    
    // Render the final markdown with toggle
    this._render_markdown(accumulatedText, targetLanguage);
  }

  _update_streaming_display(text) {
    // Render markdown progressively as text streams in
    const renderedHtml = this._render_markdown_progressive(text);
    
    const html = `
      <div style="padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333;">
        <div style="font-size: 14px; color: #2196f3; margin-bottom: 10px; font-weight: 500;">
          ✨ Generating explanation...
          <span style="display: inline-block; width: 3px; height: 15px; background: #2196f3; margin-left: 2px; animation: blink 1s infinite;"></span>
        </div>
        <div class="markdown-content">${renderedHtml}</div>
        <style>
          @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
          }
          .markdown-content h1 { 
            font-size: 18px; 
            font-weight: bold; 
            color: #333; 
            margin: 15px 0 10px 0; 
            border-bottom: 2px solid #2196f3; 
            padding-bottom: 5px; 
          }
          .markdown-content h2 { 
            font-size: 16px; 
            font-weight: bold; 
            color: #2196f3; 
            margin: 12px 0 8px 0; 
          }
          .markdown-content strong { 
            font-weight: bold; 
          }
          .markdown-content em { 
            font-style: italic; 
          }
        </style>
      </div>
    `;
    this._set_frame_content(html);
  }

  _render_markdown_progressive(markdownText) {
    // Render markdown syntax to HTML as it arrives
    return markdownText
      // Headers (only complete lines)
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      // Bold text (must be complete **text**)
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      // Italic text (must be complete *text*)
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      // Line breaks
      .replace(/\n/g, '<br>');
  }

  _render_markdown(markdownText, targetLanguage) {
    // Use the same progressive rendering for consistency
    const renderedHtml = this._render_markdown_progressive(markdownText);
    
    // Determine the toggle text based on current language
    const bookLangName = (typeof LUTE_BOOK_LANGUAGE !== 'undefined' && LUTE_BOOK_LANGUAGE.name) ? LUTE_BOOK_LANGUAGE.name : 'Target Language';
    const isTargetLanguage = targetLanguage !== 'English';
    const toggleText = isTargetLanguage ? `Switch explanations to English` : `Switch explanations to ${bookLangName}`;
    
    const finalHtml = `
      <div style="padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333;">
        <div style="margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #e0e0e0;">
          <span style="font-size: 14px; color: #666;">✨ AI Explanation</span>
        </div>
        <div class="markdown-content">${renderedHtml}</div>
        <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #e0e0e0; text-align: center;">
          <a href="#" id="ai-lang-toggle" 
             style="font-size: 13px; color: #2196f3; text-decoration: none; cursor: pointer;">
            ${toggleText}
          </a>
        </div>
        <style>
          .markdown-content h1 { 
            font-size: 18px; 
            font-weight: bold; 
            color: #333; 
            margin: 15px 0 10px 0; 
            border-bottom: 2px solid #2196f3; 
            padding-bottom: 5px; 
          }
          .markdown-content h2 { 
            font-size: 16px; 
            font-weight: bold; 
            color: #2196f3; 
            margin: 12px 0 8px 0; 
          }
          .markdown-content strong { 
            font-weight: bold; 
          }
          .markdown-content em { 
            font-style: italic; 
          }
        </style>
      </div>
    `;
    this._set_frame_content(finalHtml);
    
    // Attach click handler after content is rendered
    this._attachToggleHandler();
  }

  _attachToggleHandler() {
    // Wait for the iframe to load, then attach the click handler
    const frame = this.frame;
    
    const attachHandler = () => {
      try {
        const toggleLink = frame.contentDocument.getElementById('ai-lang-toggle');
        if (toggleLink) {
          toggleLink.addEventListener('click', (e) => {
            e.preventDefault();
            this._handleLanguageToggle();
          });
        }
      } catch (e) {
        console.error('Error attaching toggle handler:', e);
      }
    };
    
    // If iframe is already loaded, attach immediately
    if (frame.contentDocument && frame.contentDocument.readyState === 'complete') {
      attachHandler();
    } else {
      // Otherwise wait for load event
      frame.addEventListener('load', attachHandler, { once: true });
    }
  }

  _handleLanguageToggle() {
    // Toggle the language preference
    const currentUseTarget = LUTE_USER_SETTINGS.ai_explanation_use_target_language;
    const newUseTarget = !currentUseTarget;
    
    // Update the user setting
    LUTE_USER_SETTINGS.ai_explanation_use_target_language = newUseTarget;
    
    // Save the preference to the server
    this._saveLanguagePreference(newUseTarget);
    
    // Get the new target language
    const bookLangName = (typeof LUTE_BOOK_LANGUAGE !== 'undefined' && LUTE_BOOK_LANGUAGE.name) ? LUTE_BOOK_LANGUAGE.name : 'Target Language';
    const newTargetLang = newUseTarget ? bookLangName : 'English';
    
    // Update current target language
    AIExplainButton.currentTargetLanguage = newTargetLang;
    
    // Re-fetch the explanation with the new language
    const text = AIExplainButton.currentText;
    if (text) {
      // Clear the cache for this text to force re-fetch
      const oldCacheKey = this._get_cache_key(text, currentUseTarget ? bookLangName : 'English');
      AIExplainButton.explanationCache.delete(oldCacheKey);
      
      // Fetch with new language
      this._fetch_explanation(text, newTargetLang);
    }
  }

  _saveLanguagePreference(useTargetLanguage) {
    // Save the preference to the server via settings API
    // The endpoint is /settings/set/<key>/<value>
    const value = useTargetLanguage ? '1' : '0';
    fetch(`/settings/set/ai_explanation_use_target_language/${value}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.result !== 'success') {
        console.error('Failed to save language preference:', data.message);
      }
    })
    .catch(error => {
      console.error('Error saving language preference:', error);
    });
  }

  static handleLanguageToggle() {
    // This is kept for backward compatibility but should not be used via onclick
    // The instance method _handleLanguageToggle() is used instead
    const aiButton = LookupButton.all.find(b => b instanceof AIExplainButton);
    if (aiButton) {
      aiButton._handleLanguageToggle();
    }
  }

  _show_streaming_loading() {
    const html = `
      <div style="padding: 40px 20px; text-align: center; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="font-size: 32px; margin-bottom: 15px; animation: pulse 2s infinite;">✨</div>
        <div style="font-size: 18px; color: #333; font-weight: 500; margin-bottom: 8px;">AI is warming up...</div>
        <div style="font-size: 14px; color: #666; margin-bottom: 20px;">This may take a few seconds</div>
        <div style="display: flex; justify-content: center; gap: 4px;">
          <div style="width: 8px; height: 8px; background: #3498db; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both;"></div>
          <div style="width: 8px; height: 8px; background: #3498db; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; animation-delay: 0.16s;"></div>
          <div style="width: 8px; height: 8px; background: #3498db; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; animation-delay: 0.32s;"></div>
        </div>
        <style>
          @keyframes pulse {
            0%, 100% { opacity: 0.6; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.1); }
          }
          @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
          }
        </style>
      </div>
    `;
    this._set_frame_content(html);
  }

  _show_loading() {
    const html = `
      <div style="padding: 20px; text-align: center; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="font-size: 24px; margin-bottom: 10px;">✨</div>
        <div style="font-size: 16px; color: #666;">Generating explanation...</div>
        <div style="margin-top: 15px;">
          <div style="display: inline-block; width: 30px; height: 30px; border: 3px solid #f3f3f3; border-top: 3px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        </div>
        <style>
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        </style>
      </div>
    `;
    this._set_frame_content(html);
  }

  _show_not_configured_message() {
    const html = `
      <div style="padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; padding: 15px;">
          <div style="font-weight: bold; margin-bottom: 10px; color: #856404;">⚙️ AI Service Not Configured</div>
          <div style="color: #856404; line-height: 1.5;">
            To enable AI explanations, set the <code style="background: #f5f5f5; padding: 2px 6px; border-radius: 3px;">ANTHROPIC_API_KEY</code> environment variable with your MiniMax API key.
          </div>
        </div>
      </div>
    `;
    this._set_frame_content(html);
  }

  _show_message(message) {
    const html = `
      <div style="padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="background: #e7f3ff; border: 1px solid #2196f3; border-radius: 4px; padding: 15px; color: #0d47a1;">
          ${message}
        </div>
      </div>
    `;
    this._set_frame_content(html);
  }

  _show_error(message) {
    const html = `
      <div style="padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="background: #ffebee; border: 1px solid #f44336; border-radius: 4px; padding: 15px;">
          <div style="font-weight: bold; margin-bottom: 10px; color: #c62828;">❌ Error</div>
          <div style="color: #c62828;">${message}</div>
        </div>
      </div>
    `;
    this._set_frame_content(html);
  }

  _render_explanation(explanation) {
    const html = `
      <div style="padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333;">
        
        <div style="margin-bottom: 20px;">
          <div style="font-weight: bold; font-size: 14px; color: #666; margin-bottom: 5px;">Translation:</div>
          <div style="font-size: 16px; font-weight: 500;">${this._escape_html(explanation.short_translation)}</div>
        </div>

        ${this._format_literal_gloss(explanation.literal_gloss)}

        ${explanation.meaning_in_context ? `
        <div style="margin-bottom: 20px;">
          <div style="font-weight: bold; font-size: 14px; color: #666; margin-bottom: 5px;">Meaning in Context:</div>
          <div>${this._escape_html(explanation.meaning_in_context)}</div>
        </div>
        ` : ''}

        ${explanation.grammar_notes && explanation.grammar_notes.length > 0 ? `
        <div style="margin-bottom: 20px;">
          <div style="font-weight: bold; font-size: 14px; color: #666; margin-bottom: 8px;">Grammar Notes:</div>
          <ul style="margin: 0; padding-left: 20px;">
            ${explanation.grammar_notes.map(note => `<li style="margin-bottom: 5px;">${this._escape_html(note)}</li>`).join('')}
          </ul>
        </div>
        ` : ''}

        ${explanation.alternatives && explanation.alternatives.length > 0 ? `
        <div style="margin-bottom: 20px;">
          <div style="font-weight: bold; font-size: 14px; color: #666; margin-bottom: 5px;">Alternatives:</div>
          <div style="background: #f0f7ff; padding: 10px; border-radius: 4px; border-left: 3px solid #2196f3;">
            ${explanation.alternatives.map(alt => this._escape_html(alt)).join(' • ')}
          </div>
        </div>
        ` : ''}

        ${explanation.usage_notes ? `
        <div style="margin-bottom: 20px;">
          <div style="font-weight: bold; font-size: 14px; color: #666; margin-bottom: 5px;">Usage Notes:</div>
          <div style="color: #555;">${this._escape_html(explanation.usage_notes)}</div>
        </div>
        ` : ''}

        ${explanation.confidence !== undefined ? `
        <div style="margin-top: 25px; padding-top: 15px; border-top: 1px solid #e0e0e0; font-size: 13px; color: #999;">
          Confidence: ${this._get_confidence_indicator(explanation.confidence)}
        </div>
        ` : ''}
      </div>
    `;
    this._set_frame_content(html);
  }

  _escape_html(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  _get_confidence_indicator(confidence) {
    if (confidence >= 0.9) return '🟢 Very High';
    if (confidence >= 0.75) return '🟢 High';
    if (confidence >= 0.6) return '🟡 Medium';
    return '🟠 Low';
  }

  _format_literal_gloss(literal_gloss) {
    if (!literal_gloss) return '';
    
    // Handle object format: { "Es": "It/There", "hatte": "had", ... }
    if (typeof literal_gloss === 'object') {
      const parts = Object.entries(literal_gloss).map(([word, meaning]) => {
        return `${this._escape_html(word)} (${this._escape_html(meaning)})`;
      });
      return `
        <div style="margin-bottom: 20px; background: #f8f9fa; padding: 12px; border-radius: 4px;">
          <div style="font-weight: bold; font-size: 14px; color: #666; margin-bottom: 5px;">Literal Breakdown:</div>
          <div style="font-style: italic; color: #555;">${parts.join(' | ')}</div>
        </div>
      `;
    }
    
    // Handle string format
    return `
      <div style="margin-bottom: 20px; background: #f8f9fa; padding: 12px; border-radius: 4px;">
        <div style="font-weight: bold; font-size: 14px; color: #666; margin-bottom: 5px;">Literal Breakdown:</div>
        <div style="font-style: italic; color: #555;">${this._escape_html(literal_gloss)}</div>
      </div>
    `;
  }

  _set_frame_content(html) {
    const doc = this.frame.contentDocument || this.frame.contentWindow.document;
    doc.open();
    doc.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <style>
          body { margin: 0; padding: 0; }
        </style>
      </head>
      <body>
        ${html}
      </body>
      </html>
    `);
    doc.close();
  }

}  // end AIExplainButton


/**
 * A "dictionary button" to be shown in the UI.
 * Manages display state, loading and caching content.
 *
 * The class *could* be broken up into things like
 * PopupDictButton, EmbeddedDictButton, etc, but no need for that yet.
 */
class DictButton extends LookupButton {

  constructor(dictURL, frameName) {
    super(frameName);

    this.dictID = LookupButton.TERM_DICTS.indexOf(dictURL);
    if (this.dictID == -1) {
      console.log(`Error: Dict url ${dictURL} not found (??)`);
      return;
    }

    const url = dictURL.split("*").splice(-1)[0];

    this.label = (url.length <= 10) ? url : (url.slice(0, 10) + '...');

    // If the URL is a real url, get icon and label.
    let fimg = null;
    try {
      const urlObj = new URL(url);  // Throws if invalid.
      const domain = urlObj.hostname;
      this.label = domain.split("www.").splice(-1)[0];

      fimg = document.createElement("img");
      fimg.classList.add("dict-btn-fav-img");
      const favicon_src = `http://www.google.com/s2/favicons?domain=${domain}`;
      fimg.src = favicon_src;
    }
    catch(err) {}

    this.btn.textContent = this.label;

    // Must prepend after the textContent is set, or it is overwritten/lost.
    if (fimg != null)
      this.btn.prepend(fimg);

    this.btn.setAttribute("title", this.label);

    this.isExternal = (dictURL.charAt(0) == '*');
    if (this.isExternal) {
      const ext_img = document.createElement("img");
      ext_img.classList.add("dict-btn-external-img");
      this.btn.classList.add("dict-btn-external");
      this.btn.appendChild(ext_img);
    }
  }

  /** LOOKUPS *************************/

  do_lookup() {
    const dicturl = LookupButton.TERM_DICTS[this.dictID];
    if (LookupButton.TERM_FORM_CONTAINER == null || dicturl == null)
      return;
    const term = LookupButton.TERM_FORM_CONTAINER.querySelector("#text").value;
    if (this.isExternal) {
      this._load_popup(dicturl, term);
    }
    else {
      this._load_frame(dicturl, term);
    }
    this.activate();
  }

  _get_lookup_url(dicturl, term) {
    let ret = dicturl;
    // Terms are saved with zero-width space between each token;
    // remove that for dict searches.
    const zeroWidthSpace = '\u200b';
    const sqlZWS = '%E2%80%8B';
    const cleantext = term.
          replaceAll(zeroWidthSpace, '').
          replace(/\s+/g, ' ');
    const searchterm = encodeURIComponent(cleantext).
          replaceAll(sqlZWS, '');
    ret = ret.replace('[LUTE]', searchterm);
    ret = ret.replace('###', searchterm);  // TODO remove_old_###_placeholder
    return ret;
  }

  _load_popup(url, term) {
    if ((url ?? "") == "")
      return;
    if (url[0] == "*")  // Should be true!
      url = url.slice(1);
    const lookup_url = this._get_lookup_url(url, term);
    let settings = 'width=800, height=600, scrollbars=yes, menubar=no, resizable=yes, status=no'
    if (LUTE_USER_SETTINGS.open_popup_in_new_tab)
      settings = null;
    window.open(lookup_url, 'otherwin', settings);
  }

  _load_frame(dicturl, text) {
    if (this.isExternal || this.dictID == null) {
      return;
    }
    if (this.contentLoaded) {
      console.log(`${this.label} content already loaded.`);
      return;
    }

    let url = this._get_lookup_url(dicturl, text);

    const is_bing_image_search = (dicturl.indexOf('www.bing.com/images') != -1);
    if (is_bing_image_search) {
      // TODO handle_image_lookup_separately: don't mix term lookups with image lookups.
      let use_text = text;
      const binghash = dicturl.replace('https://www.bing.com/images/search?', '');
      url = `/bing/search/${LookupButton.LANG_ID}/${encodeURIComponent(use_text)}/${encodeURIComponent(binghash)}`;
    }

    this.frame.setAttribute("src", url);
    this.contentLoaded = true;
  }

}  // end DictButton


/**
 * Load excess buttons in a separate div.
 */
function _create_dict_dropdown_div(buttons_in_list) {
  // div containing all the buttons_in_list.
  const list_div = document.createElement("div");
  list_div.setAttribute("id", "dict-list-container");
  list_div.classList.add("dict-list-hide");
  buttons_in_list.forEach(button => {
    button.btn.classList.remove("dict-btn");
    button.btn.classList.add("dict-menu-item");
    list_div.appendChild(button.btn);
  });

  // Top level button to show/hide the list.
  const btn = document.createElement("button");
  btn.classList.add("dict-btn", "dict-btn-select");
  btn.innerHTML = "&hellip; &#9660;"
  btn.setAttribute("title", "More dictionaries");
  btn.addEventListener("click", (e) => {
    list_div.classList.toggle("dict-list-hide");
  });

  const menu_div = document.createElement("div");
  menu_div.setAttribute("id", "dict-menu-container");
  menu_div.appendChild(list_div);
  menu_div.appendChild(btn);
  menu_div.addEventListener("mouseleave", () => {
    list_div.classList.add("dict-list-hide");
  });

  return menu_div;
}

/**
 * Check if AI explanation service is available.
 */
function checkAIServiceStatus() {
  fetch('/api/explain/status')
    .then(response => response.json())
    .then(data => {
      AIExplainButton.isConfigured = data.available === true;
      if (data.available) {
        console.log('AI explanation service available:', data.provider, data.model);
      } else {
        console.log('AI explanation service not configured');
      }
    })
    .catch(error => {
      console.log('AI explanation service check failed:', error);
      AIExplainButton.isConfigured = false;
    });
}

/**
 * Create all buttons.
 */
function createLookupButtons(tab_count = 5) {
  let destroy_existing_dictTab_controls = function() {
    document.querySelectorAll(".dict-btn").forEach(item => item.remove())
    document.querySelectorAll(".dictframe").forEach(item => item.remove())
    const el = document.getElementById("dict-menu-container");
    if (el)
      el.remove();
  }
  destroy_existing_dictTab_controls();
  LookupButton.all = [];

  if (LookupButton.TERM_DICTS.length <= 0) return;

  // const dev_hack_add_dicts = Array.from({ length: 5 }, (_, i) => `a${i}`);
  // LookupButton.TERM_DICTS.push(...dev_hack_add_dicts);

  if (tab_count == (LookupButton.TERM_DICTS.length - 1)) {
    // Don't bother making a list with a single item.
    tab_count += 1;
  }

  // Make all DictButtons first, which loads LookupButton.all.
  LookupButton.TERM_DICTS.forEach((dict, index) => { new DictButton(dict,`dict${index}`); });
  
  // Add AI Explain button as the last button (appears after dictionaries)
  new AIExplainButton();
  const tab_buttons = LookupButton.all.slice(0, tab_count);
  const list_buttons = LookupButton.all.slice(tab_count);

  // Add elements to container.
  const container = document.getElementById("dicttabslayout");
  let grid_col_count = tab_buttons.length;
  tab_buttons.forEach(button => container.appendChild(button.btn));
  if (list_buttons.length > 0) {
    const dropdown_div = _create_dict_dropdown_div(list_buttons);
    container.appendChild(dropdown_div);
    grid_col_count += 1;
  }
  container.style.gridTemplateColumns = `repeat(${grid_col_count}, minmax(2rem, 8rem))`;

  // Auto-activate the first dictionary button (not AI Explain)
  const first_dict_button = LookupButton.all.find(b => !(b instanceof AIExplainButton));
  if (first_dict_button) {
    first_dict_button.activate();
    first_dict_button.do_lookup();
  }

  for (let b of [new SentenceLookupButton(), new ImageLookupButton()])
    document.getElementById("dicttabsstatic").appendChild(b.btn);

  const dictframes = document.getElementById("dictframes");
  LookupButton.all.forEach((button) => { dictframes.appendChild(button.frame); });
  
  // Check AI service status after buttons are created
  checkAIServiceStatus();
}


function loadDictionaries() {
  const dictContainer = document.querySelector(".dictcontainer");
  dictContainer.style.display = "flex";
  dictContainer.style.flexDirection = "column";
  LookupButton.all.forEach(button => button.contentLoaded = false);
  const active_button = LookupButton.all.find(button => button.is_active);
  if (active_button) {
    active_button.do_lookup();
  }
}
