<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';

  interface Props {
    content?: string;
    disabled?: boolean;
    onSave?: () => void;
    onSaved?: () => void;
    saving?: boolean;
  }

  let { content = '', disabled = false, onSave, onSaved, saving = false }: Props = $props();

  const dispatch = createEventDispatcher();

  type ValueType = 'boolean' | 'number' | 'string' | 'list';

  interface ConfigOption {
    id: string;
    key: string;
    value: any;
    type: ValueType;
    listValues: string[];
  }

  let ytDlpOptions: ConfigOption[] = $state([]);
  let customOptions: ConfigOption[] = $state([]);

  let newKey = $state('');
  let newType: ValueType = $state('string');
  let showAddYtDlp = $state(false);
  let showAddCustom = $state(false);
  let filterText = $state('');
  let ytDlpExpanded = $state(false);
  let customExpanded = $state(false);
  let ytDlpSearchText = $state('');
  let customSearchText = $state('');

  type YtDlpOptionType = 'boolean' | 'number' | 'string' | 'rate' | 'range' | 'list';

  interface YtDlpOptionDef {
    type: YtDlpOptionType;
    description: string;
  }

  const ytDlpOptionDefs: Record<string, YtDlpOptionDef> = {
    '--format': { type: 'string', description: 'Video format selector (e.g., best[height<=480])' },
    '--output': { type: 'string', description: 'Output template for filenames' },
    '--output-na-placeholder': { type: 'string', description: 'Placeholder for unavailable fields (default: NA)' },
    '--output-snippet': { type: 'boolean', description: 'Do not include number index in filename' },
    '--restrict-filenames': { type: 'boolean', description: 'Restrict filenames to ASCII characters' },
    '--no-restrict-filenames': { type: 'boolean', description: 'Allow Unicode characters in filenames' },
    '--trim-filenames': { type: 'number', description: 'Limit filename length (excluding extension)' },
    '--cookies': { type: 'string', description: 'Browser cookies file (exp: netscape format)' },
    '--no-cookies': { type: 'boolean', description: 'Do not read cookies from file' },
    '--download-archive': { type: 'string', description: 'Download archive file' },
    '--no-download-archive': { type: 'boolean', description: 'Do not use archive file' },
    '--batch-file': { type: 'string', description: 'File containing URLs to download' },
    '--no-batch-file': { type: 'boolean', description: 'Do not read URLs from batch file' },
    '--paths': { type: 'string', description: 'Paths where to save files (type:path format)' },
    '--default-search': { type: 'string', description: 'Prefix for unqualified URLs (e.g.,gvsearch)' },
    '--ignore-errors': { type: 'boolean', description: 'Ignore download/postprocessing errors' },
    '--no-abort-on-error': { type: 'boolean', description: 'Continue with next video on errors' },
    '--abort-on-error': { type: 'boolean', description: 'Abort on download error (alias: --no-ignore-errors)' },
    '--dump-user-agent': { type: 'boolean', description: 'Display current user-agent and exit' },
    '--list-extractors': { type: 'boolean', description: 'List all supported extractors and exit' },
    '--extractor-descriptions': { type: 'boolean', description: 'Output descriptions of extractors' },
    '--use-extractors': { type: 'list', description: 'Extractor names to use (comma separated)' },
    '--extractor-args': { type: 'string', description: 'Arguments for extractor (format: extractor:args)' },
    '--config-locations': { type: 'string', description: 'Location of main config file' },
    '--config-locations': { type: 'string', description: 'Location of main config file' },
    '--flat-playlist': { type: 'boolean', description: 'Do not extract videos from playlist' },
    '--no-flat-playlist': { type: 'boolean', description: 'Extract videos from playlist' },
    '--playlist-reverse': { type: 'boolean', description: 'Download playlist videos in reverse order' },
    '--no-playlist-reverse': { type: 'boolean', description: 'Download in playlist order (default)' },
    '--playlist-random': { type: 'boolean', description: 'Download playlist videos in random order' },
    '--no-playlist-random': { type: 'boolean', description: 'Download in playlist order' },
    '--lazy-playlist': { type: 'boolean', description: 'Process playlist entries when needed' },
    '--no-lazy-playlist': { type: 'boolean', description: 'Process all entries upfront' },
    '--wait-for-video': { type: 'range', description: 'Wait for scheduled streams (min[-max] seconds)' },
    '--playlist-items': { type: 'string', description: 'Playlist items to download (e.g.,1:3,7,-5::2)' },
    '--match-filters': { type: 'list', description: 'Generic video filter (comma separated filters)' },
    '--no-match-filters': { type: 'boolean', description: 'Do not use any match filter' },
    '--break-on-existing': { type: 'boolean', description: 'Stop when file already exists' },
    '--break-per-input': { type: 'boolean', description: 'Alters --max-downloads, --break-on-existing' },
    '--skip-playlist-after-errors': { type: 'number', description: 'Skip playlist after N errors' },
    '--no-skip-playlist-after-errors': { type: 'boolean', description: 'Do not skip playlist on errors' },
    '--playlist-start': { type: 'number', description: 'Playlist video to start at (default: 1)' },
    '--playlist-end': { type: 'number', description: 'Playlist video to end at (default: last)' },
    '--max-downloads': { type: 'number', description: 'Abort after downloading N files' },
    '--min-filesize': { type: 'string', description: 'Abort if filesize smaller than SIZE (e.g.,50k)' },
    '--max-filesize': { type: 'string', description: 'Abort if filesize larger than SIZE' },
    '--date': { type: 'string', description: 'Download only videos uploaded on this date' },
    '--datebefore': { type: 'string', description: 'Download only videos uploaded on or before date' },
    '--dateafter': { type: 'string', description: 'Download only videos uploaded on or after date' },
    '--min-views': { type: 'number', description: 'Do not download videos with less than N views' },
    '--max-views': { type: 'number', description: 'Do not download videos with more than N views' },
    '--match-title': { type: 'list', description: 'Download only matching titles (regex or substring)' },
    '--reject-title': { type: 'list', description: 'Skip download if title matches regex' },
    '--age-limit': { type: 'number', description: 'Download only videos suitable for age (years)' },
    '--download-sections': { type: 'string', description: 'Download only chapters matching regex' },
    '--include-ads': { type: 'boolean', description: 'Include advertisements' },
    '--no-include-ads': { type: 'boolean', description: 'Do not include advertisements (default)' },
    '--limit-rate': { type: 'rate', description: 'Maximum download rate (e.g.,50K or 4.2M)' },
    '--throttled-rate': { type: 'rate', description: 'Minimum rate below which throttling is assumed' },
    '--retries': { type: 'number', description: 'Number of retries (default:10) or "infinite"' },
    '--file-access-retries': { type: 'number', description: 'Number of retries on file access error' },
    '--fragment-retries': { type: 'number', description: 'Number of retries for fragments (default:10)' },
    '--retry-sleep': { type: 'range', description: 'Sleep between retries (type:expr format)' },
    '--skip-unavailable-fragments': { type: 'boolean', description: 'Skip unavailable fragments' },
    '--no-skip-unavailable-fragments': { type: 'boolean', description: 'Do not skip fragments (default)' },
    '--concurrent-fragments': { type: 'number', description: 'Number of fragments to download concurrently' },
    '--buffer-size': { type: 'string', description: 'Size of download buffer (e.g.,1024 or 16K)' },
    '--no-resize-buffer': { type: 'boolean', description: 'Do not automatically adjust buffer size' },
    '--http-chunk-size': { type: 'number', description: 'Size of HTTP chunk for downloading (bytes)' },
    '--sleep-interval': { type: 'range', description: 'Seconds to wait between downloads' },
    '--max-sleep-interval': { type: 'range', description: 'Maximum seconds to wait' },
    '--sleep-requests': { type: 'number', description: 'Seconds to wait between requests' },
    '--no-external-downloader': { type: 'boolean', description: 'Do not use external downloader' },
    '--external-downloader': { type: 'string', description: 'External downloader to use (e.g.,aria2c)' },
    '--external-downloader-args': { type: 'string', description: 'Arguments for external downloader' },
    '--proxy': { type: 'string', description: 'HTTP/HTTPS/SOCKS proxy URL' },
    '--socket-timeout': { type: 'number', description: 'Time to wait before giving up (seconds)' },
    '--source-address': { type: 'string', description: 'Client-side IP address to bind to' },
    '--impersonate': { type: 'string', description: 'Client to impersonate (e.g.,chrome)' },
    '--list-impersonate-targets': { type: 'boolean', description: 'List available impersonation targets' },
    '--user-agent': { type: 'string', description: 'Specify user agent string' },
    '--referer': { type: 'string', description: 'Referer URL to use' },
    '--add-headers': { type: 'string', description: 'Custom headers to use (header:value format)' },
    '--no-check-certificate': { type: 'boolean', description: 'Suppress SSL certificate verification' },
    '--check-certificate': { type: 'boolean', description: 'Verify SSL certificates (default)' },
    '--client-sertificate': { type: 'string', description: 'Path to client certificate file' },
    '--no-check-hostname': { type: 'boolean', description: 'Do not verify SSL hostname' },
    '--check-hostname': { type: 'boolean', description: 'Verify SSL hostname (default)' },
    '--no-provider-sertificate-chain': { type: 'boolean', description: 'Do not verify provider certificate chain' },
    '--legacy-server-support': { type: 'boolean', description: 'Use legacy SSL/TLS support' },
    '--no-warnings': { type: 'boolean', description: 'Do not show warnings' },
    '--quiet': { type: 'boolean', description: 'Activate quiet mode' },
    '--no-quiet': { type: 'boolean', description: 'Deactivate quiet mode (default)' },
    '--no-progress': { type: 'boolean', description: 'Do not print progress bar' },
    '--progress': { type: 'boolean', description: 'Show progress bar (default)' },
    '--console-title': { type: 'boolean', description: 'Display progress in console title' },
    '--progress-template': { type: 'string', description: 'Template for progress prints' },
    '-v': { type: 'boolean', description: 'Short for --verbose' },
    '--verbose': { type: 'boolean', description: 'Print various debugging information' },
    '--dump-pages': { type: 'boolean', description: 'Print downloaded pages to stdout (debug)' },
    '--write-pages': { type: 'boolean', description: 'Write downloaded pages to files (debug)' },
    '--print': { type: 'string', description: 'Print template to screen (when:template)' },
    '--print-to-file': { type: 'string', description: 'Print template to file (when:template:filename)' },
    '--newline': { type: 'boolean', description: 'Print new line per progress' },
    '--no-color': { type: 'boolean', description: 'Do not emit color codes in output' },
    '--color': { type: 'string', description: 'Color policy (when:stream:policy)' },
    '--simulate': { type: 'boolean', description: 'Do not download, only print info' },
    '--no-simulate': { type: 'boolean', description: 'Download (default)' },
    '--skip-download': { type: 'boolean', description: 'Do not download files' },
    '--no-skip-download': { type: 'boolean', description: 'Download (default)' },
    '--force-download-archive': { type: 'boolean', description: 'Force using archive file even if already used' },
    '--force-overwrites': { type: 'boolean', description: 'Overwrite all video and metadata files' },
    '--no-force-overwrites': { type: 'boolean', description: 'Do not overwrite (default)' },
    '--dry-run': { type: 'boolean', description: 'Do not download, same as --simulate --skip-download' },
    '--no-mtime': { type: 'boolean', description: 'Do not set file modification time' },
    '--mtime': { type: 'boolean', description: 'Use file modification time from info.json (default)' },
    '--no-continue': { type: 'boolean', description: 'Do not resume partial downloads' },
    '--continue': { type: 'boolean', description: 'Resume partial downloads (default)' },
    '--no-part': { type: 'boolean', description: 'Do not use .part files' },
    '--part': { type: 'boolean', description: 'Use .part files (default)' },
    '--no-clean-infojson': { type: 'boolean', description: 'Keep HTML fields in infojson' },
    '--clean-infojson': { type: 'boolean', description: 'Remove private fields from infojson' },
    '--no-keep-video': { type: 'boolean', description: 'Do not keep video file after postprocessing' },
    '--keep-video': { type: 'boolean', description: 'Keep video file after postprocessing' },
    '--no-post-overwrites': { type: 'boolean', description: 'Do not overwrite postprocessed files' },
    '--post-overwrites': { type: 'boolean', description: 'Overwrite postprocessed files (default)' },
    '--no-prepare-stdout': { type: 'boolean', description: 'Do not prepare stdout for writing' },
    '--embed-thumbnail': { type: 'boolean', description: 'Embed thumbnail in video' },
    '--no-embed-thumbnail': { type: 'boolean', description: 'Do not embed thumbnail' },
    '--write-thumbnail': { type: 'boolean', description: 'Download thumbnails' },
    '--no-write-thumbnail': { type: 'boolean', description: 'Do not write thumbnails' },
    '--write-info-json': { type: 'boolean', description: 'Write video info JSON file' },
    '--no-write-info-json': { type: 'boolean', description: 'Do not write info JSON' },
    '--write-annotations': { type: 'boolean', description: 'Write video annotations' },
    '--no-write-annotations': { type: 'boolean', description: 'Do not write annotations' },
    '--write-description': { type: 'boolean', description: 'Write video description' },
    '--no-write-description': { type: 'boolean', description: 'Do not write description' },
    '--write-link': { type: 'boolean', description: 'Write internet shortcut (.desktop) file' },
    '--write-url-link': { type: 'boolean', description: 'Write .url shortcut file' },
    '--write-webloc-link': { type: 'boolean', description: 'Write .webloc macOS shortcut' },
    '--write-desktop-link': { type: 'boolean', description: 'Write .desktop Linux shortcut' },
    '--extract-audio': { type: 'boolean', description: 'Convert video to audio only' },
    '--audio-format': { type: 'string', description: 'Audio format (best, mp3, m4a, opus, vorbis, wav)' },
    '--audio-quality': { type: 'string', description: 'Audio quality (0=best, 9=worst for mp3)' },
    '--remux-video': { type: 'string', description: 'Remux video into container (e.g.,mp4)' },
    '--recode-video': { type: 'string', description: 'Recode video to format (e.g.,mp4)' },
    '--postprocessor-args': { type: 'string', description: 'Arguments for postprocessor' },
    '--keep-metadata': { type: 'boolean', description: 'Keep metadata in original format' },
    '--no-keep-metadata': { type: 'boolean', description: 'Normalize metadata (default)' },
    '--embed-metadata': { type: 'boolean', description: 'Embed metadata to video' },
    '--no-embed-metadata': { type: 'boolean', description: 'Do not embed metadata' },
    '--add-metadata': { type: 'boolean', description: 'Add metadata to file' },
    '--no-add-metadata': { type: 'boolean', description: 'Do not add metadata' },
    '--embed-chapters': { type: 'boolean', description: 'Add chapter markers' },
    '--no-embed-chapters': { type: 'boolean', description: 'Do not add chapters' },
    '--embed-info-json': { type: 'boolean', description: 'Embed infojson to video' },
    '--no-embed-info-json': { type: 'boolean', description: 'Do not embed infojson' },
    '--parse-metadata': { type: 'string', description: 'Parse additional metadata (from:to)' },
    '--replace-in-metadata': { type: 'string', description: 'Replace metadata (field:regex;repl)' },
    '--xattrs': { type: 'boolean', description: 'Write metadata to xattrs' },
    '--concat-playlist': { type: 'string', description: 'Playlist concatenation method (manual, merge, plusequal)' },
    '--fixup': { type: 'string', description: 'Fixup streaming issues (never, warn, detect, always)' },
    '--js-runtime': { type: 'string', description: 'JavaScript runtime to use (deno:/path/to/deno)' },
    '--no-js-runtime': { type: 'boolean', description: 'Do not use JavaScript runtime' },
    '--extractor-retries': { type: 'number', description: 'Number of retries for extractor (default:3)' },
    '--allow-unrecoverable-exception': { type: 'boolean', description: 'Allow unrecoverable exceptions' },
    '--no-allow-unrecoverable-exception': { type: 'boolean', description: 'Fail on unrecoverable exception (default)' },
    '--reattempt-exit': { type: 'number', description: 'Exit with this code on unrecoverable errors' },
    '--no-check-formats': { type: 'boolean', description: 'Do not check available formats' },
    '--check-formats': { type: 'boolean', description: 'Check available formats (default)' },
    '--format-sort': { type: 'list', description: 'Sort formats by criteria (e.g.,hasvid,vext,aext)' },
    '--format-sort-force': { type: 'boolean', description: 'Force sorting by criteria' },
    '--no-format-sort-force': { type: 'boolean', description: 'Do not force sort (default)' },
    '--format': { type: 'string', description: 'Video format selector (short for -f)' },
    '-f': { type: 'string', description: 'Video format selector' },
    '-F': { type: 'boolean', description: 'List available formats' },
    '--list-formats': { type: 'boolean', description: 'List available video formats' },
    '--list-subs': { type: 'boolean', description: 'List available subtitles' },
    '--sub-format': { type: 'string', description: 'Subtitle format (ass/srt/best)' },
    '--sub-langs': { type: 'list', description: 'Subtitle languages to download (e.g.,en,ar,fr)' },
    '--write-subs': { type: 'boolean', description: 'Write subtitle file' },
    '--write-auto-subs': { type: 'boolean', description: 'Write auto-generated subtitles' },
    '--no-write-subs': { type: 'boolean', description: 'Do not write subtitles' },
    '--no-write-auto-subs': { type: 'boolean', description: 'Do not write auto subs' },
    '--embed-subs': { type: 'boolean', description: 'Embed subtitles in video' },
    '--no-embed-subs': { type: 'boolean', description: 'Do not embed subtitles' },
    '--list-thnails': { type: 'boolean', description: 'List available thumbnails' },
    '--convert-thumbnails': { type: 'string', description: 'Convert thumbnails to format' },
    '--no-convert-thumbnails': { type: 'boolean', description: 'Do not convert thumbnails' },
    '--prefer-free-formats': { type: 'boolean', description: 'Prefer free non-DRM formats' },
    '--no-prefer-free-formats': { type: 'boolean', description: 'Prefer non-free formats' },
    '--check-all-formats': { type: 'boolean', description: 'Check all formats for availability' },
    '--no-check-all-formats': { type: 'boolean', description: 'Only check selected formats' },
    '--prefer-merge-formats': { type: 'string', description: 'Prefer merging over single streams' },
    '--video-multistreams': { type: 'boolean', description: 'Allow multiple video streams' },
    '--no-video-multistreams': { type: 'boolean', description: 'Only one video stream (default)' },
    '--audio-multistreams': { type: 'boolean', description: 'Allow multiple audio streams' },
    '--no-audio-multistreams': { type: 'boolean', description: 'Only one audio stream (default)' },
    '--no-plalist': { type: 'boolean', description: 'Treat URLs as single video' },
    '--yes-playlist': { type: 'boolean', description: 'Download playlist if URL is playlist' },
    '--no-playlist': { type: 'boolean', description: 'Do not download playlist' },
    '--mark-watched': { type: 'boolean', description: 'Mark videos as watched' },
    '--no-mark-watched': { type: 'boolean', description: 'Do not mark as watched' },
    '--no-colors': { type: 'boolean', description: 'Disable color output' },
    '--compat-options': { type: 'string', description: 'Compatibility options' },
    '--alias': { type: 'string', description: 'Create alias for option string' },
    '--update': { type: 'boolean', description: 'Update to latest version' },
    '--no-update': { type: 'boolean', description: 'Do not check for updates (default)' },
    '--update-to': { type: 'string', description: 'Upgrade/downgrade to specific version' },
    '--help': { type: 'boolean', description: 'Print help text' },
    '-h': { type: 'boolean', description: 'Print help text (short)' },
    '--extractor': { type: 'string', description: 'Extractor to use (legacy)' },
    '--url': { type: 'boolean', description: 'Generic downloader' },
    '--type': { type: 'string', description: 'Downloader type (http, fragment)' },
    '--fragment-scheme': { type: 'string', description: 'Fragment download scheme (basic, beta)' },
    '--test': { type: 'boolean', description: 'Test download (same as --dry-run)' },
  };

  const customOptionDefs: Record<string, YtDlpOptionDef> = {
    '--poster': { type: 'boolean', description: 'Generate folder poster image' },
    '--random-agent': { type: 'boolean', description: 'Rotate user agents' },
    '--download-timeout': { type: 'number', description: 'Max time per video (seconds)' },
    '--stall-timeout': { type: 'number', description: 'Stall timeout (seconds)' },
    '--upgrade': { type: 'boolean', description: 'Upgrade yt-dlp before downloading' },
    '--max-videos': { type: 'number', description: 'Max videos to download (0=unlimited)' },
    '--max-duration': { type: 'number', description: 'Max session duration (seconds)' }
  };

  const ytDlpQuickAdd = Object.keys(ytDlpOptionDefs).sort();
  const customQuickAdd = Object.keys(customOptionDefs).sort();

  function generateId(): string {
    return Math.random().toString(36).substring(2, 9);
  }

  function getYtDlpType(key: string): YtDlpOptionType {
    return ytDlpOptionDefs[key]?.type || 'string';
  }

  function detectType(key: string, value: any): ValueType {
    if (typeof value === 'boolean') return 'boolean';
    if (typeof value === 'number') return 'number';
    if (typeof value === 'string') {
      if (key.includes('reject') || key.includes('filter') || key.includes('match')) return 'list';
      if (value.includes('|')) return 'list';
      const defType = ytDlpOptionDefs[key]?.type || customOptionDefs[key]?.type;
      if (defType === 'rate' || defType === 'range') return 'string';
      return 'string';
    }
    return 'string';
  }

  function parseListValue(value: string): string[] {
    if (!value) return [];
    return value.split('|').map(v => v.trim()).filter(v => v);
  }

  function serializeListValue(values: string[]): string {
    return values.join('|');
  }

  function parseContent() {
    let parsed: any = {};
    try {
      parsed = JSON.parse(content);
    } catch (e) {
      parsed = { 'yt-dlp': {}, 'custom': {} };
    }

    const ytDlpData = parsed['yt-dlp'] || {};
    const customData = parsed['custom'] || {};

    ytDlpOptions = Object.entries(ytDlpData).map(([key, value]) => {
      const defType = ytDlpOptionDefs[key]?.type || 'string';
      let type: ValueType = 'string';
      if (defType === 'boolean') type = 'boolean';
      else if (defType === 'number') type = 'number';
      else if (defType === 'list' || defType === 'rate' || defType === 'range') type = 'list';
      else type = detectType(key, value);
      
      return {
        id: generateId(),
        key,
        value: type === 'list' ? serializeListValue(parseListValue(value as string)) : value,
        type,
        listValues: type === 'list' ? parseListValue(value as string) : []
      };
    });

    customOptions = Object.entries(customData).map(([key, value]) => {
      const type = detectType(key, value);
      return {
        id: generateId(),
        key,
        value: type === 'list' ? serializeListValue(parseListValue(value as string)) : value,
        type,
        listValues: type === 'list' ? parseListValue(value as string) : []
      };
    });
  }

  function emitChange() {
    const ytDlpData: Record<string, any> = {};
    const customData: Record<string, any> = {};

    ytDlpOptions.forEach(opt => {
      if (opt.key && opt.key.trim()) {
        if (opt.type === 'list') {
          ytDlpData[opt.key] = serializeListValue(opt.listValues);
        } else if (opt.value !== undefined && opt.value !== '') {
          ytDlpData[opt.key] = opt.value;
        }
      }
    });

    customOptions.forEach(opt => {
      if (opt.key && opt.key.trim()) {
        if (opt.type === 'list') {
          customData[opt.key] = serializeListValue(opt.listValues);
        } else if (opt.value !== undefined && opt.value !== '') {
          customData[opt.key] = opt.value;
        }
      }
    });

    dispatch('change', { 'yt-dlp': ytDlpData, 'custom': customData });
  }

  function isKeyDuplicate(section: 'yt-dlp' | 'custom', key: string): boolean {
    const normalizedKey = key.startsWith('--') ? key : `--${key}`;
    const options = section === 'yt-dlp' ? ytDlpOptions : customOptions;
    return options.some(o => o.key === normalizedKey);
  }

  function quickAddOption(section: 'yt-dlp' | 'custom', key: string) {
    if (key && isKeyDuplicate(section, key)) return;

    let defType: YtDlpOptionType = 'string';
    let defaultValue: any = true;
    let listValues: string[] = [];
    
    if (section === 'yt-dlp' && key) {
      defType = ytDlpOptionDefs[key]?.type || 'string';
    } else if (section === 'custom' && key) {
      defType = customOptionDefs[key]?.type || 'string';
    }

    if (defType === 'string' || defType === 'rate' || defType === 'range') {
      defaultValue = '';
    } else if (defType === 'number') {
      defaultValue = 0;
    } else if (defType === 'list') {
      defaultValue = '';
      listValues = [];
    }

    let type: ValueType = 'string';
    if (defType === 'boolean') type = 'boolean';
    else if (defType === 'number') type = 'number';
    else if (defType === 'list' || defType === 'rate' || defType === 'range') type = 'list';

    const option: ConfigOption = {
      id: generateId(),
      key: key || '',
      value: defaultValue,
      type,
      listValues
    };

    if (section === 'yt-dlp') {
      ytDlpOptions = [option, ...ytDlpOptions];
    } else {
      customOptions = [option, ...customOptions];
    }
    emitChange();
  }

  function addEmptyOption(section: 'yt-dlp' | 'custom') {
    if (section === 'yt-dlp') {
      ytDlpExpanded = true;
    } else {
      customExpanded = true;
    }
    quickAddOption(section, '');
    if (section === 'yt-dlp') {
      showAddYtDlp = false;
      ytDlpSearchText = '';
    } else {
      showAddCustom = false;
      customSearchText = '';
    }
  }

  function removeOption(section: 'yt-dlp' | 'custom', id: string) {
    if (section === 'yt-dlp') {
      ytDlpOptions = ytDlpOptions.filter(o => o.id !== id);
    } else {
      customOptions = customOptions.filter(o => o.id !== id);
    }
    emitChange();
  }

  function updateKey(section: 'yt-dlp' | 'custom', id: string, newKey: string) {
    const options = section === 'yt-dlp' ? ytDlpOptions : customOptions;
    const idx = options.findIndex(o => o.id === id);
    if (idx !== -1) {
      options[idx].key = newKey.startsWith('--') ? newKey : `--${newKey}`;
      if (section === 'yt-dlp') ytDlpOptions = [...options];
      else customOptions = [...options];
      emitChange();
    }
  }

  function updateType(section: 'yt-dlp' | 'custom', id: string, newType: ValueType) {
    const options = section === 'yt-dlp' ? ytDlpOptions : customOptions;
    const idx = options.findIndex(o => o.id === id);
    if (idx !== -1) {
      const opt = options[idx];
      opt.type = newType;
      if (newType === 'boolean') opt.value = true;
      else if (newType === 'number') opt.value = 0;
      else if (newType === 'string') opt.value = '';
      else if (newType === 'list') { opt.value = ''; opt.listValues = []; }
      if (section === 'yt-dlp') ytDlpOptions = [...options];
      else customOptions = [...options];
      emitChange();
    }
  }

  function updateValue(section: 'yt-dlp' | 'custom', id: string, value: any) {
    const options = section === 'yt-dlp' ? ytDlpOptions : customOptions;
    const idx = options.findIndex(o => o.id === id);
    if (idx !== -1) {
      options[idx].value = value;
      if (section === 'yt-dlp') ytDlpOptions = [...options];
      else customOptions = [...options];
      emitChange();
    }
  }

  function addListValue(section: 'yt-dlp' | 'custom', id: string, value: string) {
    if (!value.trim()) return;
    const options = section === 'yt-dlp' ? ytDlpOptions : customOptions;
    const idx = options.findIndex(o => o.id === id);
    if (idx !== -1 && !options[idx].listValues.includes(value.trim())) {
      options[idx].listValues = [...options[idx].listValues, value.trim()];
      options[idx].value = serializeListValue(options[idx].listValues);
      if (section === 'yt-dlp') ytDlpOptions = [...options];
      else customOptions = [...options];
      emitChange();
    }
  }

  function removeListValue(section: 'yt-dlp' | 'custom', id: string, index: number) {
    const options = section === 'yt-dlp' ? ytDlpOptions : customOptions;
    const idx = options.findIndex(o => o.id === id);
    if (idx !== -1) {
      options[idx].listValues = options[idx].listValues.filter((_, i) => i !== index);
      options[idx].value = serializeListValue(options[idx].listValues);
      if (section === 'yt-dlp') ytDlpOptions = [...options];
      else customOptions = [...options];
      emitChange();
    }
  }

  let filteredYtDlp = $derived(
    filterText.trim()
      ? ytDlpOptions.filter(o => o.key.toLowerCase().includes(filterText.toLowerCase()))
      : ytDlpOptions
  );

  let filteredCustom = $derived(
    filterText.trim()
      ? customOptions.filter(o => o.key.toLowerCase().includes(filterText.toLowerCase()))
      : customOptions
  );

  let filteredYtDlpQuickAdd = $derived(
    ytDlpSearchText.trim()
      ? ytDlpQuickAdd.filter(o => o.toLowerCase().includes(ytDlpSearchText.toLowerCase()))
      : ytDlpQuickAdd
  );

  let filteredCustomQuickAdd = $derived(
    customSearchText.trim()
      ? customQuickAdd.filter(o => o.toLowerCase().includes(customSearchText.toLowerCase()))
      : customQuickAdd
  );

  function handleClickOutside(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.dropdown-wrapper')) {
      showAddYtDlp = false;
      showAddCustom = false;
    }
  }

  $effect(() => {
    parseContent();
  });

  export function getContent(): string {
    return content;
  }

  export function setContent(newContent: string) {
    content = newContent;
    parseContent();
  }

  onMount(() => {
    parseContent();
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  });
</script>

<div class="config-editor">
  <div class="header">
    {#if onSave}
      <button class="action-btn save-btn" onclick={() => { onSave?.(); onSaved?.(); }} disabled={saving || disabled}>
        <span class="btn-icon">💾</span>
        {saving ? 'Saving...' : 'Save'}
      </button>
    {/if}
    <div class="header-spacer"></div>
    <div class="header-right">
      <input
        type="text"
        class="filter-input"
        placeholder="Filter options..."
        bind:value={filterText}
      />
      <div class="dropdown-wrapper">
        <button class="action-btn blue" onclick={(e) => { e.stopPropagation(); showAddYtDlp = !showAddYtDlp; showAddCustom = false; }} {disabled}>
          <span class="btn-icon">⚡</span>
          Add yt-dlp
        </button>
        {#if showAddYtDlp}
          <div class="dropdown quick-add">
            <div class="dropdown-search">
              <input
                type="text"
                class="dropdown-filter"
                placeholder="Filter arguments..."
                bind:value={ytDlpSearchText}
                onclick={(e) => e.stopPropagation()}
              />
            </div>
            <button class="dropdown-item empty-option" onclick={() => addEmptyOption('yt-dlp')}>
              — Empty —
            </button>
            {#each filteredYtDlpQuickAdd as opt}
              {@const isDup = isKeyDuplicate('yt-dlp', opt)}
              <button 
                class="dropdown-item" 
                class:duplicate={isDup}
                onclick={() => !isDup && quickAddOption('yt-dlp', opt)}
                disabled={isDup}
                title={ytDlpOptionDefs[opt]?.description || ''}
              >
                {opt}
                {#if isDup}
                  <span class="dup-badge">✓</span>
                {/if}
              </button>
            {/each}
          </div>
        {/if}
      </div>
      <div class="dropdown-wrapper">
        <button class="action-btn purple" onclick={(e) => { e.stopPropagation(); showAddCustom = !showAddCustom; showAddYtDlp = false; }} {disabled}>
          <span class="btn-icon">✨</span>
          Add Custom
        </button>
        {#if showAddCustom}
          <div class="dropdown quick-add">
            <div class="dropdown-search">
              <input
                type="text"
                class="dropdown-filter"
                placeholder="Filter arguments..."
                bind:value={customSearchText}
                onclick={(e) => e.stopPropagation()}
              />
            </div>
            <button class="dropdown-item empty-option" onclick={() => addEmptyOption('custom')}>
              — Empty —
            </button>
            {#each filteredCustomQuickAdd as opt}
              {@const isDup = isKeyDuplicate('custom', opt)}
              <button 
                class="dropdown-item" 
                class:duplicate={isDup}
                onclick={() => !isDup && quickAddOption('custom', opt)}
                disabled={isDup}
                title={customOptionDefs[opt]?.description || ''}
              >
                {opt}
                {#if isDup}
                  <span class="dup-badge">✓</span>
                {/if}
              </button>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </div>

  <div class="section">
    <div class="section-header" onclick={() => ytDlpExpanded = !ytDlpExpanded}>
      <h4>
        <span class="expand-icon">{ytDlpExpanded ? '▼' : '▶'}</span>
        yt-dlp Options
        {#if ytDlpOptions.length > 0}
          <span class="count">({ytDlpOptions.length})</span>
        {/if}
      </h4>
    </div>

    {#if ytDlpExpanded}
      <div class="options-list">
        {#each filteredYtDlp as option (option.id)}
          <div class="option-card">
            <div class="option-row-main">
              <input
                type="text"
                class="key-input"
                placeholder="--option-name"
                value={option.key}
                oninput={(e) => updateKey('yt-dlp', option.id, e.currentTarget.value)}
                {disabled}
              />
              <select
                class="type-select"
                value={option.type}
                onchange={(e) => updateType('yt-dlp', option.id, e.currentTarget.value as ValueType)}
                {disabled}
              >
                <option value="boolean">Boolean</option>
                <option value="string">String</option>
                <option value="number">Number</option>
                <option value="list">List</option>
              </select>
              
              {#if option.type === 'boolean'}
                <label class="switch">
                  <input
                    type="checkbox"
                    checked={!!option.value}
                    onchange={(e) => updateValue('yt-dlp', option.id, e.currentTarget.checked)}
                    {disabled}
                  />
                  <span class="slider"></span>
                </label>
              {:else if option.type === 'number'}
                <input
                  type="number"
                  class="value-input number"
                  value={option.value}
                  oninput={(e) => updateValue('yt-dlp', option.id, parseInt(e.currentTarget.value) || 0)}
                  {disabled}
                />
              {:else if option.type === 'list'}
                <div class="list-container">
                  <div class="chips">
                    {#each option.listValues as chip, idx}
                      <span class="chip">
                        {chip}
                        <button class="chip-remove" onclick={() => removeListValue('yt-dlp', option.id, idx)} {disabled}>×</button>
                      </span>
                    {/each}
                  </div>
                  <input
                    type="text"
                    class="list-input"
                    placeholder="Add value... (press Enter)"
                    onkeydown={(e) => { if (e.key === 'Enter') { addListValue('yt-dlp', option.id, e.currentTarget.value); e.currentTarget.value = ''; } }}
                    {disabled}
                  />
                </div>
              {:else}
                <input
                  type="text"
                  class="value-input"
                  placeholder="Value"
                  value={option.value}
                  oninput={(e) => updateValue('yt-dlp', option.id, e.currentTarget.value)}
                  {disabled}
                />
              {/if}

              <button class="remove-btn" onclick={() => removeOption('yt-dlp', option.id)} {disabled}>×</button>
            </div>
          </div>
        {/each}

        {#if filteredYtDlp.length === 0}
          <div class="empty-state">
            <p>No yt-dlp options configured.</p>
            <p class="empty-hint">Click "Add yt-dlp" to add options.</p>
          </div>
        {/if}
      </div>
    {/if}
  </div>

  <div class="section">
    <div class="section-header" onclick={() => customExpanded = !customExpanded}>
      <h4>
        <span class="expand-icon">{customExpanded ? '▼' : '▶'}</span>
        Custom Options
        {#if customOptions.length > 0}
          <span class="count">({customOptions.length})</span>
        {/if}
      </h4>
    </div>

    {#if customExpanded}
      <div class="options-list">
        {#each filteredCustom as option (option.id)}
          <div class="option-card">
            <div class="option-row-main">
              <input
                type="text"
                class="key-input purple-key"
                placeholder="--option-name"
                value={option.key}
                oninput={(e) => updateKey('custom', option.id, e.currentTarget.value)}
                {disabled}
              />
              <select
                class="type-select"
                value={option.type}
                onchange={(e) => updateType('custom', option.id, e.currentTarget.value as ValueType)}
                {disabled}
              >
                <option value="boolean">Boolean</option>
                <option value="string">String</option>
                <option value="number">Number</option>
                <option value="list">List</option>
              </select>
              
              {#if option.type === 'boolean'}
                <label class="switch">
                  <input
                    type="checkbox"
                    checked={!!option.value}
                    onchange={(e) => updateValue('custom', option.id, e.currentTarget.checked)}
                    {disabled}
                  />
                  <span class="slider"></span>
                </label>
              {:else if option.type === 'number'}
                <input
                  type="number"
                  class="value-input number"
                  value={option.value}
                  oninput={(e) => updateValue('custom', option.id, parseInt(e.currentTarget.value) || 0)}
                  {disabled}
                />
              {:else if option.type === 'list'}
                <div class="list-container">
                  <div class="chips">
                    {#each option.listValues as chip, idx}
                      <span class="chip purple-chip">
                        {chip}
                        <button class="chip-remove" onclick={() => removeListValue('custom', option.id, idx)} {disabled}>×</button>
                      </span>
                    {/each}
                  </div>
                  <input
                    type="text"
                    class="list-input"
                    placeholder="Add value... (press Enter)"
                    onkeydown={(e) => { if (e.key === 'Enter') { addListValue('custom', option.id, e.currentTarget.value); e.currentTarget.value = ''; } }}
                    {disabled}
                  />
                </div>
              {:else}
                <input
                  type="text"
                  class="value-input"
                  placeholder="Value"
                  value={option.value}
                  oninput={(e) => updateValue('custom', option.id, e.currentTarget.value)}
                  {disabled}
                />
              {/if}

              <button class="remove-btn" onclick={() => removeOption('custom', option.id)} {disabled}>×</button>
            </div>
          </div>
        {/each}

        {#if filteredCustom.length === 0}
          <div class="empty-state">
            <p>No custom options configured.</p>
            <p class="empty-hint">Click "Add Custom" to add options.</p>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .config-editor {
    width: 100%;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    flex-wrap: wrap;
    gap: 12px;
  }

  .header-spacer {
    flex: 1;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .filter-input {
    padding: 8px 14px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    color: white;
    font-size: 13px;
    width: 180px;
  }

  .filter-input:focus {
    outline: none;
    border-color: #3b82f6;
  }

  .filter-input::placeholder {
    color: #6b7280;
  }

  .action-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    cursor: pointer;
    transition: background 0.15s;
  }

  .save-btn {
    background: #3b82f6;
    color: white;
  }

  .save-btn:hover:not(:disabled) {
    background: #2563eb;
  }

  .save-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-icon {
    font-size: 14px;
  }

  .dropdown-wrapper {
    position: relative;
  }

  .action-btn.blue {
    background: #3b82f6;
    color: white;
  }

  .action-btn.blue:hover:not(:disabled) {
    background: #2563eb;
  }

  .action-btn.purple {
    background: #8b5cf6;
    color: white;
  }

  .action-btn.purple:hover:not(:disabled) {
    background: #7c3aed;
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .dropdown {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 4px;
    background: #1f2937;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    z-index: 50;
    max-height: 300px;
    overflow-y: auto;
  }

  .dropdown.quick-add {
    width: 280px;
  }

  .dropdown-search {
    padding: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
  }

  .dropdown-filter {
    width: 100%;
    padding: 8px 12px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 4px;
    color: white;
    font-size: 13px;
    box-sizing: border-box;
  }

  .dropdown-filter:focus {
    outline: none;
    border-color: #3b82f6;
  }

  .dropdown-filter::placeholder {
    color: #6b7280;
  }

  .dropdown-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    padding: 10px 14px;
    text-align: left;
    background: none;
    border: none;
    color: #d1d5db;
    font-size: 13px;
    font-family: monospace;
    cursor: pointer;
    transition: background 0.1s;
  }

  .dropdown-item:hover:not(:disabled) {
    background: rgba(255,255,255,0.1);
  }

  .dropdown-item:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .dropdown-item.duplicate {
    color: #6b7280;
  }

  .dropdown-item.empty-option {
    font-family: sans-serif;
    color: #9ca3af;
    font-style: italic;
    border-bottom: 1px solid rgba(255,255,255,0.1);
  }

  .dropdown-item.empty-option:hover {
    background: rgba(255,255,255,0.05);
  }

  .dup-badge {
    font-size: 10px;
    color: #10b981;
  }

  .section {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
  }

  .section-header {
    cursor: pointer;
    padding: 4px 0;
  }

  .section-header:hover h4 {
    color: #e5e7eb;
  }

  .section-header h4 {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
    color: #d1d5db;
    transition: color 0.15s;
  }

  .expand-icon {
    font-size: 10px;
    margin-right: 8px;
    color: #6b7280;
  }

  .count {
    font-weight: normal;
    color: #6b7280;
    font-size: 12px;
  }

  .options-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 12px;
  }

  .option-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 12px;
  }

  .option-row-main {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
  }

  .key-input {
    padding: 8px 12px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 4px;
    color: #60a5fa;
    font-size: 13px;
    font-family: monospace;
    width: 180px;
  }

  .key-input.purple-key {
    color: #a78bfa;
  }

  .key-input:focus {
    outline: none;
    border-color: #3b82f6;
  }

  .key-input:disabled {
    opacity: 0.5;
  }

  .type-select {
    padding: 8px 10px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 4px;
    color: #9ca3af;
    font-size: 12px;
    cursor: pointer;
  }

  .type-select:focus {
    outline: none;
    border-color: #3b82f6;
  }

  .type-select:disabled {
    opacity: 0.5;
  }

  .value-input {
    flex: 1;
    min-width: 120px;
    padding: 8px 12px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 4px;
    color: white;
    font-size: 13px;
  }

  .value-input:focus {
    outline: none;
    border-color: #3b82f6;
  }

  .value-input:disabled {
    opacity: 0.5;
  }

  .value-input.number {
    width: 100px;
  }

  .list-container {
    flex: 1;
    min-width: 200px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    background: rgba(59, 130, 246, 0.2);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 4px;
    color: #60a5fa;
    font-size: 12px;
    font-family: monospace;
  }

  .chip.purple-chip {
    background: rgba(139, 92, 246, 0.2);
    border-color: rgba(139, 92, 246, 0.3);
    color: #a78bfa;
  }

  .chip-remove {
    background: none;
    border: none;
    color: inherit;
    cursor: pointer;
    font-size: 14px;
    padding: 0;
    line-height: 1;
    opacity: 0.7;
  }

  .chip-remove:hover {
    opacity: 1;
  }

  .list-input {
    padding: 6px 10px;
    background: rgba(255,255,255,0.05);
    border: 1px dashed rgba(255,255,255,0.2);
    border-radius: 4px;
    color: white;
    font-size: 12px;
    width: 100%;
    box-sizing: border-box;
  }

  .list-input:focus {
    outline: none;
    border-color: #3b82f6;
    border-style: solid;
  }

  .list-input:disabled {
    opacity: 0.5;
  }

  .switch {
    position: relative;
    display: inline-block;
    width: 44px;
    height: 24px;
  }

  .switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  .slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(255,255,255,0.1);
    transition: 0.2s;
    border-radius: 24px;
  }

  .slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: 0.2s;
    border-radius: 50%;
  }

  input:checked + .slider {
    background-color: #3b82f6;
  }

  input:checked + .slider:before {
    transform: translateX(20px);
  }

  input:disabled + .slider {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .remove-btn {
    width: 28px;
    height: 28px;
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 4px;
    color: #f87171;
    cursor: pointer;
    font-size: 18px;
    line-height: 1;
    transition: all 0.15s;
  }

  .remove-btn:hover:not(:disabled) {
    background: rgba(239, 68, 68, 0.4);
  }

  .remove-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .empty-state {
    text-align: center;
    padding: 24px;
    color: #6b7280;
    font-size: 13px;
  }

  .empty-hint {
    font-size: 12px;
    margin-top: 4px;
    opacity: 0.7;
  }
</style>
