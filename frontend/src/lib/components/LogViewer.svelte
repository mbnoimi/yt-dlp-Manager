<script lang="ts">
  let {
    content = '',
    height = '400px',
    maxLines = 0,
    lineNumbers = true,
    searchable = true,
    highlightWords = [],
    theme = 'dark',
    follow = false
  } = $props();

  const LINE_HEIGHT = 20;
  const BUFFER_SIZE = 20;
  const DEFAULT_HEIGHT = 400;

  let searchQuery = $state('');
  let containerEl: HTMLDivElement;
  let userScrolledUp = $state(false);
  let prevContentLength = $state(0);
  let lastScrollTop = $state(0);

  let allLines = $derived(content.split('\n'));
  let totalLines = $derived(allLines.length);
  let totalHeight = $derived(totalLines * LINE_HEIGHT);

  let heightFromMaxLines = $derived(maxLines > 0 ? maxLines * LINE_HEIGHT : 0);
  let toolbarHeight = $derived(searchable ? 44 : 0);
  let computedHeight = $derived(
    maxLines > 0 
      ? heightFromMaxLines 
      : (() => {
          const h = parseInt(height.replace('px', ''));
          return isNaN(h) ? DEFAULT_HEIGHT : h;
        })()
  );
  let viewerHeight = $derived(computedHeight);
  let contentHeight = $derived(viewerHeight - toolbarHeight);

  let scrollTop = $state(0);

  let startIndex = $derived(Math.max(0, Math.floor(scrollTop / LINE_HEIGHT) - BUFFER_SIZE));
  let endIndex = $derived(
    Math.min(totalLines, Math.ceil((scrollTop + contentHeight) / LINE_HEIGHT) + BUFFER_SIZE)
  );

  let visibleLines = $derived(
    allLines.slice(startIndex, endIndex).map((line, i) => {
      let text = line;
      if (searchQuery) {
        const regex = new RegExp(`(${escapeRegex(searchQuery)})`, 'gi');
        text = text.replace(regex, '<mark class="bg-yellow-500/50 text-yellow-200">$1</mark>');
      }
      return { num: startIndex + i + 1, text };
    })
  );

  let topPadding = $derived(startIndex * LINE_HEIGHT);

  function escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function handleScroll(e: Event) {
    const target = e.target as HTMLDivElement;
    scrollTop = target.scrollTop;
    
    const isAtBottom = target.scrollHeight - target.scrollTop - target.clientHeight < 50;
    userScrolledUp = !isAtBottom;
    lastScrollTop = target.scrollTop;
  }

  $effect(() => {
    const newLength = content.length;
    const contentGrew = newLength > prevContentLength;
    prevContentLength = newLength;

    if (follow && contentGrew && containerEl) {
      if (!userScrolledUp) {
        requestAnimationFrame(() => {
          containerEl.scrollTop = containerEl.scrollHeight;
        });
      }
    }
  });

  $effect(() => {
    if (follow && content && containerEl && !userScrolledUp) {
      containerEl.scrollTop = containerEl.scrollHeight;
    }
  });

  function scrollToBottom() {
    if (containerEl) {
      containerEl.scrollTop = containerEl.scrollHeight;
      userScrolledUp = false;
    }
  }
</script>

<div class="log-viewer" style="height: {viewerHeight}px;">
  {#if searchable}
    <div class="log-toolbar">
      <input
        type="text"
        bind:value={searchQuery}
        placeholder="Search logs..."
        class="log-search-input"
      />
      <span class="line-count">{totalLines.toLocaleString()} lines</span>
      {#if userScrolledUp}
        <button class="follow-btn" onclick={scrollToBottom}>
          ↓ Follow
        </button>
      {/if}
    </div>
  {/if}
  
  <div 
    class="log-content {theme}" 
    bind:this={containerEl}
    onscroll={handleScroll}
    style="height: {contentHeight}px;"
  >
    <div class="log-scroll-container" style="height: {totalHeight}px;">
      <div class="log-visible-lines" style="transform: translateY({topPadding}px);">
        {#each visibleLines as line (line.num)}
          <div class="log-line" style="height: {LINE_HEIGHT}px;">
            {#if lineNumbers}
              <span class="line-number">{line.num}</span>
            {/if}
            <span class="line-text">{@html line.text}</span>
          </div>
        {/each}
      </div>
    </div>
  </div>
</div>

<style>
  .log-viewer {
    display: flex;
    flex-direction: column;
    border-radius: 8px;
    overflow: hidden;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 13px;
  }

  .log-toolbar {
    padding: 8px;
    background: #1e1e1e;
    border-bottom: 1px solid #333;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .log-search-input {
    flex: 1;
    padding: 6px 10px;
    background: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 4px;
    color: #ccc;
    font-size: 13px;
  }

  .log-search-input:focus {
    outline: none;
    border-color: #007acc;
  }

  .line-count {
    font-size: 11px;
    color: #6e7681;
    white-space: nowrap;
  }

  .follow-btn {
    padding: 4px 10px;
    background: #0d6394;
    border: none;
    border-radius: 4px;
    color: #fff;
    font-size: 12px;
    cursor: pointer;
    white-space: nowrap;
  }

  .follow-btn:hover {
    background: #0a4d7a;
  }

  .log-content {
    overflow-y: auto;
    overflow-x: auto;
    flex: 1;
  }

  .log-content.dark {
    background: #1e1e1e;
    color: #d4d4d4;
  }

  .log-content.light {
    background: #f5f5f5;
    color: #333;
  }

  .log-scroll-container {
    position: relative;
  }

  .log-visible-lines {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
  }

  .log-line {
    display: flex;
    padding: 0 8px;
    white-space: pre;
    align-items: center;
    box-sizing: border-box;
  }

  .log-line:hover {
    background: rgba(255, 255, 255, 0.05);
  }

  .line-number {
    flex-shrink: 0;
    width: 50px;
    text-align: right;
    padding-right: 12px;
    color: #6e7681;
    user-select: none;
  }

  .line-text {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: pre;
  }
</style>
