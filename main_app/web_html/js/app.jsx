// Eel Bridge Interface with browser fallback
const callEel = async (funcName, ...args) => {
  if (window.eel && typeof window.eel[funcName] === 'function') {
    try {
      return await window.eel[funcName](...args)();
    } catch (err) {
      console.error(`Eel error calling ${funcName}:`, err);
      throw err;
    }
  } else {
    console.warn(`[Dev Mode] Call to eel.${funcName}(${args.join(', ')}) simulated.`);
    if (funcName === 'get_company_list') return ['Diam Light (Shree Sai)', 'Eraya Sparkle (Meruliya)', 'Kavalier Fine jewelry (MANI)', 'Jewel Facets'];
    if (funcName === 'get_product_list') return ['Wedding Band', "Men's Ring", 'Wedding Ring Set', 'Engagement Ring', 'Pendant', 'Earrings', 'Bracelet'];
    if (funcName === 'get_all_categories') return [
      { id: 1, name: 'Wedding Band' }, { id: 2, name: "Men's Ring" }, { id: 3, name: 'Wedding Ring Set' },
      { id: 4, name: 'Engagement Ring' }, { id: 5, name: 'Pendant' }, { id: 6, name: 'Earrings' }, { id: 7, name: 'Bracelet' }
    ];
    if (funcName === 'get_all_setting_columns') return [
      { id: 1, name: 'Default' }, { id: 2, name: 'Solitaire' }, { id: 3, name: 'Eternity' }, { id: 4, name: '3 Stone' }
    ];
    if (funcName === 'get_all_subcategories') return [
      { id: 1, name: 'Default' }, { id: 2, name: 'Solitaire' }, { id: 3, name: 'Halo' }, { id: 4, name: 'Three Stone' }, { id: 5, name: 'Vintage' }
    ];
    if (funcName === 'get_all_company_policies') return [
      { id: 1, company_name: 'Diam Light (Shree Sai)', shipping_profile_name: 'Fast Shipping', brand_name: 'Diam Light', location: 'New York' },
      { id: 2, company_name: 'Eraya Sparkle (Meruliya)', shipping_profile_name: 'Standard', brand_name: 'Eraya Sparkle', location: 'USA' }
    ];
    if (funcName === 'get_all_title_templates') return [
      { id: 1, metal_type: 'gold', product_category: 'Engagement Ring', setting_column: 'Default', template_text: '{TCW} ct {CENTER_STONE_SHAPE} {GOLD_KT} {GOLD_COLOR} Engagement Ring' },
      { id: 2, metal_type: 'platinum', product_category: 'Pendant', setting_column: 'Default', template_text: '{TCW} ct {CENTER_STONE_SHAPE} Platinum Pendant' }
    ];
    if (funcName === 'get_all_placeholders') return [
      { id: 1, name: '{TCW}', description: 'Total Carat Weight' },
      { id: 2, name: '{CENTER_STONE_SHAPE}', description: 'Center Stone Shape' },
      { id: 3, name: '{GOLD_KT}', description: 'Gold Karat Purity' },
      { id: 4, name: '{GOLD_COLOR}', description: 'Gold Metal Color' },
      { id: 5, name: '{TITLE}', description: 'Item Title' },
      { id: 6, name: '{SKU}', description: 'Item SKU' }
    ];
    if (funcName === 'get_all_company_html_templates') return [
      { id: 1, company_name: 'Diam Light (Shree Sai)', category: 'Engagement Ring', subcategory: 'Default', html_template: '<div class="listing"><title>{TITLE}</title><h1>{TITLE}</h1></div>' }
    ];
    if (funcName === 'get_all_excel_mappings') return [
      { id: 1, source_sheet: 'RING', source_column: 'SKU', target_sheet: 'Cat-EngagementRings', target_column: 'Custom label (SKU)', mapping_type: 'direct', default_value: '' },
      { id: 2, source_sheet: 'RING', source_column: 'TOTAL_DIAMOND_PCS', target_sheet: 'Cat-EngagementRings', target_column: 'C:Total Diamond Pieces', mapping_type: 'direct', default_value: '' },
      { id: 3, source_sheet: 'PENDANT', source_column: 'SKU', target_sheet: 'Cat-NecklacesPendants', target_column: 'Custom label (SKU)', mapping_type: 'direct', default_value: '' }
    ];
    if (funcName === 'get_data_file_sheets') return ['RING', 'EARRINGS', 'PENDANT', 'BRACELET'];
    if (funcName === 'get_target_file_sheets') return ['Cat-EngagementRings', 'Cat-WeddingAnniversaryBands', 'Cat-EngagementWeddingRingSets', 'Cat-Earrings', 'Cat-NecklacesPendants', 'Cat-BraceletsCharms', 'Cat-Rings'];
    if (funcName === 'sync_excel_mappings') return true;
    if (funcName === 'backup_database') return { status: 'success', message: 'Simulated backup created successfully!', filename: 'app_database_backup_simulated.db' };
    if (funcName === 'list_database_backups') return [{ filename: 'app_database_backup_simulated.db', created_at: '2026-08-09 04:40:00', size_bytes: 1925120, path: 'backups/app_database_backup_simulated.db' }];
    if (funcName === 'restore_database') return { status: 'success', message: 'Simulated restore completed successfully!' };
    if (funcName === 'schedule') return '2026-10-14T02:35:00';
    if (funcName === 'get_schedule_time') return { status: 'success', schedule_time: '2026-10-14T02:35:00', current_pdt: '2026-10-13 07:20:00 PM PDT' };
    if (funcName === 'app1') return 'Process Completed Successfully!';
    return true;
  }
};


const getFilteredTargetSheets = (sourceSheet, allTargetSheets = []) => {
  if (!sourceSheet || sourceSheet === '[ALL]' || sourceSheet === 'all') return allTargetSheets;
  const src = String(sourceSheet).toUpperCase().trim();
  if (src === 'RING' || src === 'RINGS') {
    return allTargetSheets.filter(t => 
      ['Cat-EngagementRings', 'Cat-WeddingAnniversaryBands', 'Cat-EngagementWeddingRingSets', 'Cat-Rings'].includes(t)
    );
  }
  if (src === 'EARRINGS' || src === 'EARRING') {
    return allTargetSheets.filter(t => t === 'Cat-Earrings');
  }
  if (src === 'PENDANT' || src === 'PENDANTS' || src === 'NECKLACE' || src === 'NECKLACES') {
    return allTargetSheets.filter(t => t === 'Cat-NecklacesPendants');
  }
  if (src === 'BRACELET' || src === 'BRACELETS') {
    return allTargetSheets.filter(t => t === 'Cat-BraceletsCharms');
  }
  return allTargetSheets;
};

const { useState, useEffect, useRef, useMemo } = React;

// Sample Live Preview HTML Variable Interpolator with Injected Selection & Visual ContentEditable Editor Scripts
const renderLivePreviewHtml = (rawHtml, mode = 'raw', isVisualEditing = false) => {
  const scriptTag = `
    <script>
      (function() {
        if (${isVisualEditing ? 'true' : 'false'}) {
          window.addEventListener('DOMContentLoaded', function() {
            var selectedNode = null;
            var hoverNode = null;

            var style = document.createElement('style');
            style.innerHTML = \`
              .inspect-hover-outline { outline: 2px dashed #6366f1 !important; outline-offset: -2px; cursor: pointer !important; }
              .inspect-select-outline { outline: 3px solid #8b5cf6 !important; outline-offset: -2px; background: rgba(139, 92, 246, 0.12) !important; }
              .specsHd { background-color: #0d2137 !important; color: #ffffff !important; font-weight: bold !important; padding: 6px 12px !important; text-transform: uppercase !important; display: block !important; visibility: visible !important; min-height: 24px !important; margin-bottom: 6px !important; }
              #inspect-badge {
                position: fixed;
                z-index: 999999;
                background: #4f46e5;
                color: #ffffff;
                font-family: monospace;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 6px;
                border-radius: 4px;
                pointer-events: none;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                display: none;
              }
            \`;
            document.head.appendChild(style);

            var badge = document.createElement('div');
            badge.id = 'inspect-badge';
            document.body.appendChild(badge);

            var cleanBodyHtml = function() {
              var clone = document.body.cloneNode(true);
              var b = clone.querySelector('#inspect-badge');
              if (b) b.remove();
              var elems = clone.querySelectorAll('.inspect-hover-outline, .inspect-select-outline');
              elems.forEach(function(el) {
                el.classList.remove('inspect-hover-outline', 'inspect-select-outline');
                if (el.contentEditable === 'true') el.removeAttribute('contenteditable');
              });
              if (clone.contentEditable === 'true') clone.removeAttribute('contenteditable');
              return clone.innerHTML;
            };

            var sendUpdatedHtml = function() {
              if ("${mode}" === "sample") return; // Do not overwrite raw template text when previewing sample values
              var htmlContent = cleanBodyHtml();
              if (htmlContent && !htmlContent.includes('No HTML listing template found')) {
                window.parent.postMessage({ type: 'LIVE_ELEMENT_EDIT', updatedHtml: htmlContent }, '*');
              }
            };

            var getElementPath = function(el) {
              var path = [];
              while (el && el !== document.body && el.parentElement) {
                var parent = el.parentElement;
                var children = Array.prototype.slice.call(parent.children);
                var index = children.indexOf(el);
                if (index === -1) break;
                path.unshift(index);
                el = parent;
              }
              return path;
            };

            var getElementInfo = function(node) {
              if (!node || node === document.body || node === document.documentElement) return null;
              var attrs = {};
              if (node.attributes) {
                for (var i = 0; i < node.attributes.length; i++) {
                  var a = node.attributes[i];
                  if (a.name !== 'class' || a.value.replace(/inspect-hover-outline|inspect-select-outline/g, '').trim()) {
                    attrs[a.name] = a.value;
                  }
                }
              }
              var cloneNode = node.cloneNode(true);
              cloneNode.classList.remove('inspect-hover-outline', 'inspect-select-outline');
              return {
                tagName: node.tagName,
                id: node.id || '',
                className: (node.className || '').replace(/inspect-hover-outline|inspect-select-outline/g, '').trim(),
                innerText: node.innerText || node.textContent || '',
                outerHTML: cloneNode.outerHTML || '',
                attributes: attrs,
                path: getElementPath(node)
              };
            };

            var selectElementNode = function(node) {
              if (!node || node === document.body) return;
              if (selectedNode) selectedNode.classList.remove('inspect-select-outline');
              selectedNode = node;
              selectedNode.classList.add('inspect-select-outline');
              selectedNode.contentEditable = 'true';
              
              var info = getElementInfo(selectedNode);
              if (info) {
                window.parent.postMessage({ type: 'INSPECT_ELEMENT', elementInfo: info }, '*');
              }
            };

            document.body.addEventListener('mouseover', function(e) {
              var t = e.target;
              if (!t || t === document.body || t.id === 'inspect-badge' || t.tagName === 'HTML' || t.tagName === 'SCRIPT') return;
              if (hoverNode) hoverNode.classList.remove('inspect-hover-outline');
              hoverNode = t;
              hoverNode.classList.add('inspect-hover-outline');

              var rect = t.getBoundingClientRect();
              badge.style.top = Math.max(0, rect.top - 24) + 'px';
              badge.style.left = Math.max(0, rect.left) + 'px';
              badge.textContent = t.tagName.toLowerCase() + (t.id ? '#' + t.id : '') + (t.className ? '.' + (t.className.replace(/inspect-hover-outline|inspect-select-outline/g, '').trim().split(' ').join('.')) : '');
              badge.style.display = 'block';
            }, true);

            document.body.addEventListener('mouseout', function(e) {
              if (hoverNode) {
                hoverNode.classList.remove('inspect-hover-outline');
                hoverNode = null;
              }
              badge.style.display = 'none';
            }, true);

            document.body.addEventListener('click', function(e) {
              var t = e.target;
              if (!t || t === document.body || t.id === 'inspect-badge') return;
              e.preventDefault();
              e.stopPropagation();
              selectElementNode(t);
            }, true);

            document.body.addEventListener('input', function() {
              if (selectedNode) {
                var info = getElementInfo(selectedNode);
                if (info) window.parent.postMessage({ type: 'INSPECT_ELEMENT', elementInfo: info }, '*');
              }
              sendUpdatedHtml();
            });

            // Listen for postMessage commands from Parent Window
            window.addEventListener('message', function(msgEvent) {
              var data = msgEvent.data;
              if (!data) return;

              if (data.type === 'EXEC_INSPECT_UPDATE' && selectedNode) {
                if (data.field === 'innerText') {
                  selectedNode.innerText = data.value;
                } else if (data.field === 'className') {
                  selectedNode.className = data.value + ' inspect-select-outline';
                } else if (data.field === 'outerHTML') {
                  try {
                    var temp = document.createElement('div');
                    temp.innerHTML = data.value;
                    if (temp.firstElementChild) {
                      var replacement = temp.firstElementChild;
                      selectedNode.replaceWith(replacement);
                      selectElementNode(replacement);
                    }
                  } catch(err) { console.error('OuterHTML edit error:', err); }
                }
                sendUpdatedHtml();
              } else if (data.type === 'EXEC_INSPECT_DELETE' && selectedNode) {
                var p = selectedNode.parentElement;
                selectedNode.remove();
                selectedNode = null;
                sendUpdatedHtml();
                if (p && p !== document.body) selectElementNode(p);
                else window.parent.postMessage({ type: 'INSPECT_ELEMENT', elementInfo: null }, '*');
              } else if (data.type === 'EXEC_INSPECT_PARENT' && selectedNode) {
                var par = selectedNode.parentElement;
                if (par && par !== document.body) {
                  selectElementNode(par);
                }
              }
            });
          });
        }
      })();
    </script>
  `;

  if (!rawHtml || !rawHtml.trim()) {
    return `
      ${scriptTag}
      <div style="display:flex;align-items:center;justify-content:center;height:100vh;background:#0f172a;color:#94a3b8;font-family:sans-serif;font-size:14px;text-align:center;">
        <div>
          <div style="font-size:24px;margin-bottom:8px;">⚠️</div>
          <div>No HTML listing template found for this company, category & subcategory.</div>
          <div style="font-size:12px;margin-top:4px;color:#64748b;">Type or paste HTML code on the left to live preview.</div>
        </div>
      </div>
    `;
  }

  let processed = rawHtml;
  if (mode === 'sample') {
    processed = processed
      .replaceAll('{TITLE}', '2.50 Ct Lab Grown Diamond Engagement Ring 14K White Gold')
      .replaceAll('{SKU}', 'JF-10025-EG')
      .replaceAll('{TCW}', '2.50')
      .replaceAll('{GOLD_KT}', '14K')
      .replaceAll('{GOLD_COLOR}', 'White')
      .replaceAll('{METEL}', 'Gold')
      .replaceAll('{CERTIFICATE}', 'IGI Certified')
      .replaceAll('{CENTER_STONE_SHAPE}', 'Round')
      .replaceAll('{CENTER_STONE_WEIGHT}', '2.00')
      .replaceAll('{DIAMOND_CLARITY}', 'VS1')
      .replaceAll('{DIAMOND_COLOR}', 'F')
      .replaceAll('{SIDE_STONE_SHAPE}', 'Round')
      .replaceAll('{SIDE_STONE_WEIGHT}', '0.50')
      .replaceAll('{center_stone_spec}', 'Stone Details')
      .replaceAll('{CENTER_STONE_SPEC}', 'Stone Details')
      .replaceAll('{SIDE_CLARITY}', 'VS1')
      .replaceAll('{SIDE_COLOR}', 'F')
      .replaceAll('{hide}', '')
      .replaceAll('{center_stone_spec}', 'Main Stone Details')
      .replaceAll('{CertificateGradingclass}', '');
  } else {
    processed = processed
      .replaceAll('{hide}', '')
      .replaceAll('{center_stone_spec}', 'Main Stone Details')
      .replaceAll('{CertificateGradingclass}', '');
  }

  const placeholderImg = 'https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=600';
  const placeholderThumb = 'https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=150';

  for (let i = 1; i <= 5; i++) {
    processed = processed.replaceAll(`IMG_${i}`, placeholderImg);
    processed = processed.replaceAll(`THUMB_${i}`, placeholderThumb);
  }

  return processed + scriptTag;
};

function App() {
  const [activeTab, setActiveTab] = useState('generator'); // 'generator' | 'database' | 'settings'
  const [dbSubTab, setDbSubTab] = useState('policies'); // 'policies' | 'templates' | 'html_templates' | 'categories' | 'products'

  const [companies, setCompanies] = useState([]);
  const [products, setProducts] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState('');
  const [selectedProduct, setSelectedProduct] = useState('');
  const [colorVariation, setColorVariation] = useState(false);
  const [goldPurityVariation, setGoldPurityVariation] = useState(false);
  
  const [isProcessing, setIsProcessing] = useState(false);
  const [processStatus, setProcessStatus] = useState(null);
  const [latestExportFilename, setLatestExportFilename] = useState('');
  const [catalogSyncInfo, setCatalogSyncInfo] = useState(null);
  const [companyBlueprintInfo, setCompanyBlueprintInfo] = useState(null);
  const [blueprintsMap, setBlueprintsMap] = useState({});
  const [isClearing, setIsClearing] = useState(false);
  const [clearStatus, setClearStatus] = useState(false);

  // Schedule Time States (Replaces legacy Schedule time.py)
  const [scheduleTime, setScheduleTime] = useState('');
  const [scheduleDays, setScheduleDays] = useState(0);
  const [scheduleHours, setScheduleHours] = useState(7);
  const [scheduleMinutes, setScheduleMinutes] = useState(15);
  const [scheduleCopied, setScheduleCopied] = useState(false);
  const [showScheduleSettings, setShowScheduleSettings] = useState(false);

  const calculateScheduleTimestamp = (d, h, m) => {
    try {
      const now = new Date();
      const parts = new Intl.DateTimeFormat('en-US', {
        timeZone: 'America/Los_Angeles',
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit', second: '2-digit',
        hour12: false
      }).formatToParts(now);
      const map = Object.fromEntries(parts.map(p => [p.type, p.value]));
      const pdt = new Date(Date.UTC(+map.year, +map.month - 1, +map.day, +map.hour, +map.minute, +map.second));
      pdt.setUTCDate(pdt.getUTCDate() + parseInt(d || 0, 10));
      pdt.setUTCHours(pdt.getUTCHours() + parseInt(h || 0, 10));
      pdt.setUTCMinutes(pdt.getUTCMinutes() + parseInt(m || 0, 10));
      pdt.setUTCSeconds(0);
      return pdt.toISOString().slice(0, 19);
    } catch (err) {
      console.error('Error calculating schedule timestamp:', err);
      return '';
    }
  };

  useEffect(() => {
    const update = () => {
      setScheduleTime(calculateScheduleTimestamp(scheduleDays, scheduleHours, scheduleMinutes));
    };
    update();
    const interval = setInterval(update, 10000);
    return () => clearInterval(interval);
  }, [scheduleDays, scheduleHours, scheduleMinutes]);

  const handleCopySchedule = (val) => {
    const textToCopy = val || scheduleTime;
    if (!textToCopy) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(textToCopy).then(() => {
        setScheduleCopied(true);
        setTimeout(() => setScheduleCopied(false), 2000);
      });
    } else {
      prompt('Copy Schedule Time:', textToCopy);
    }
  };


  // Database Tab States
  const [policies, setPolicies] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [placeholders, setPlaceholders] = useState([]);
  const [dbCategories, setDbCategories] = useState([]);
  const [dbSettingColumns, setDbSettingColumns] = useState([]);
  const [dbSubcategories, setDbSubcategories] = useState([]);
  const [dbBackupsList, setDbBackupsList] = useState([]);
  const [isDbOperationPending, setIsDbOperationPending] = useState(false);

  const fetchBackupsList = async () => {
    try {
      const list = await callEel('list_database_backups');
      setDbBackupsList(list || []);
    } catch (e) {
      console.error('Error fetching backups:', e);
    }
  };

  const [showCustomizeNavModal, setShowCustomizeNavModal] = useState(false);
  const [tempNavLabels, setTempNavLabels] = useState(navLabels);
  const [showBackupCreateModal, setShowBackupCreateModal] = useState(false);
  const [backupDescriptionInput, setBackupDescriptionInput] = useState('');
  const [collapsedNavPanels, setCollapsedNavPanels] = useState({});

  const handleNavTabClick = (tabKey) => {
    if (activeTab === tabKey) {
      setCollapsedNavPanels(prev => ({
        ...prev,
        [tabKey]: !prev[tabKey]
      }));
    } else {
      setActiveTab(tabKey);
      setCollapsedNavPanels(prev => ({
        ...prev,
        [tabKey]: false
      }));
    }
  };

  const handleCreateDbBackup = async (descOverride) => {
    setIsDbOperationPending(true);
    try {
      const desc = descOverride !== undefined ? descOverride : backupDescriptionInput;
      const res = await callEel('backup_database', desc.trim());
      if (res && res.status === 'success') {
        showToast(res.message, 'success');
        setBackupDescriptionInput('');
        fetchBackupsList();
      } else {
        showToast((res && res.message) || 'Backup failed', 'error');
      }
    } catch (e) {
      showToast(`Backup error: ${e.message}`, 'error');
    } finally {
      setIsDbOperationPending(false);
    }
  };

  const handleDeleteBackupFile = async (filename) => {
    if (!isAdminMode) {
      showToast('Admin Mode required to delete items! Double-click logo to unlock.', 'warning');
      return;
    }
    if (!window.confirm(`Are you sure you want to delete backup file "${filename}"?`)) return;
    try {
      const res = await callEel('delete_backup', filename);
      if (res && res.status === 'success') {
        showToast(res.message, 'info');
        fetchBackupsList();
      } else {
        showToast((res && res.message) || 'Failed to delete backup', 'error');
      }
    } catch (err) {
      showToast('Error deleting backup file', 'error');
    }
  };

  const handleEditBackupNote = (backupObj) => {
    setEditModalConfig({
      title: 'Edit Backup Description',
      label: 'Backup Note / Description:',
      initialValue: backupObj.description || '',
      onSave: async (newNote) => {
        try {
          await callEel('save_backup_note', backupObj.filename, newNote);
          showToast(`Description updated for ${backupObj.filename}`, 'success');
          fetchBackupsList();
        } catch (err) {
          showToast('Failed to save description note', 'error');
        }
      }
    });
  };

  const handleRestoreFromFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (!window.confirm(`Are you sure you want to restore database from "${file.name}"? Current data will be replaced (a safety snapshot will be taken first).`)) {
      e.target.value = '';
      return;
    }

    setIsDbOperationPending(true);
    try {
      const reader = new FileReader();
      reader.onload = async (evt) => {
        const b64 = evt.target.result;
        const res = await callEel('restore_database', null, b64);
        if (res && res.status === 'success') {
          showToast(res.message, 'success');
          if (typeof loadDatabaseData === 'function') loadDatabaseData();
          fetchBackupsList();
        } else {
          showToast((res && res.message) || 'Restore failed', 'error');
        }
        setIsDbOperationPending(false);
      };
      reader.readAsDataURL(file);
    } catch (err) {
      showToast(`Restore error: ${err.message}`, 'error');
      setIsDbOperationPending(false);
    }
    e.target.value = '';
  };

  const handleRestoreFromPath = async (path) => {
    if (!window.confirm(`Are you sure you want to restore database from backup file? Current data will be replaced (a safety snapshot will be created first).`)) {
      return;
    }
    setIsDbOperationPending(true);
    try {
      const res = await callEel('restore_database', path, null);
      if (res && res.status === 'success') {
        showToast(res.message, 'success');
        if (typeof loadDatabaseData === 'function') loadDatabaseData();
        fetchBackupsList();
      } else {
        showToast((res && res.message) || 'Restore failed', 'error');
      }
    } catch (e) {
      showToast(`Restore error: ${e.message}`, 'error');
    } finally {
      setIsDbOperationPending(false);
    }
  };
  
  // Excel Mapping Tab States
  const [excelMappings, setExcelMappings] = useState([]);
  const [availableInputSheets, setAvailableInputSheets] = useState(['RING', 'EARRINGS', 'PENDANT', 'BRACELET']);
  const [availableTargetSheets, setAvailableTargetSheets] = useState(['Cat-EngagementRings', 'Cat-WeddingAnniversaryBands', 'Cat-EngagementWeddingRingSets', 'Cat-Earrings', 'Cat-NecklacesPendants', 'Cat-BraceletsCharms', 'Cat-Rings']);
  const [mappingFilterCompany, setMappingFilterCompany] = useState('all');
  const [mappingFilterSource, setMappingFilterSource] = useState('all');
  const [mappingFilterTarget, setMappingFilterTarget] = useState('all');
  const [mappingFilterColumn, setMappingFilterColumn] = useState('all');
  const [mappingSortBy, setMappingSortBy] = useState('alpha_target_col');
  const [mappingSearch, setMappingSearch] = useState('');

  const availableTargetColumns = useMemo(() => {
    const cols = new Set();
    (excelMappings || []).forEach(m => {
      if (m.target_column && m.target_column.trim()) {
        cols.add(m.target_column.trim());
      }
    });
    return Array.from(cols).sort((a, b) => a.localeCompare(b));
  }, [excelMappings]);
  const [customPlaceholders, setCustomPlaceholders] = useState([
    '{GOLD_KT}', '{GOLD_COLOR}', '{TCW}', '{CENTER_STONE_SHAPE}', 
    '{TITLE}', '{SKU}', '{BRAND_NAME}', '{SELLING_PRICE_USD}', 
    '{CENTER_STONE_WEIGHT}', '{SETTING}', '{DIAMOND_COLOR}', '{DIAMOND_CLARITY}'
  ]);
  const [newPlaceholderInput, setNewPlaceholderInput] = useState('');
  const defaultValueInputRef = useRef(null);

  const handleInsertPlaceholder = (phTag) => {
    const inputEl = defaultValueInputRef.current;
    const currentVal = editingMapping?.default_value || '';
    
    if (inputEl) {
      const start = inputEl.selectionStart ?? currentVal.length;
      const end = inputEl.selectionEnd ?? currentVal.length;
      
      const newVal = currentVal.substring(0, start) + phTag + currentVal.substring(end);
      setEditingMapping({ ...editingMapping, default_value: newVal });
      
      setTimeout(() => {
        inputEl.focus();
        const newCursorPos = start + phTag.length;
        inputEl.setSelectionRange(newCursorPos, newCursorPos);
      }, 50);
    } else {
      setEditingMapping({ ...editingMapping, default_value: currentVal + phTag });
    }
  };

  const handleAddCustomPlaceholder = (e) => {
    if (e && e.preventDefault) e.preventDefault();
    let tag = newPlaceholderInput.trim();
    if (!tag) return;
    if (!tag.startsWith('{')) tag = '{' + tag;
    if (!tag.endsWith('}')) tag = tag + '}';
    
    if (!customPlaceholders.includes(tag)) {
      setCustomPlaceholders([...customPlaceholders, tag]);
    }
    setNewPlaceholderInput('');
  };

  const handleRemoveCustomPlaceholder = (tagToRemove) => {
    setCustomPlaceholders(customPlaceholders.filter(p => p !== tagToRemove));
  };

  const [showMappingModal, setShowMappingModal] = useState(false);
  const [editingMapping, setEditingMapping] = useState(null);
  const [selectedMappingAction, setSelectedMappingAction] = useState(null);

  const loadAvailableSheets = async () => {
    try {
      const inSheets = await callEel('get_data_file_sheets');
      if (Array.isArray(inSheets) && inSheets.length > 0) setAvailableInputSheets(inSheets);
      const tgtSheets = await callEel('get_target_file_sheets');
      if (Array.isArray(tgtSheets) && tgtSheets.length > 0) setAvailableTargetSheets(tgtSheets);
    } catch (err) {
      console.error('Error loading available sheets:', err);
    }
  };

  const loadExcelMappings = async () => {
    try {
      await loadAvailableSheets();
      const res = await callEel('get_all_excel_mappings');
      if (Array.isArray(res)) setExcelMappings(res);
    } catch (err) {
      console.error('Error loading Excel mappings:', err);
    }
  };

  const handleRefreshSheets = async () => {
    try {
      await callEel('sync_excel_mappings');
      await loadAvailableSheets();
      await loadExcelMappings();
      showToast('Synced sheets with data.xlsx!', 'success');
    } catch (err) {
      showToast('Error refreshing sheets', 'error');
    }
  };

  const openCatalogForParty = (partyId, partyName) => {
    if (window.parent && typeof window.parent.openPartyCatalogSamePage === 'function') {
      window.parent.openPartyCatalogSamePage(partyId, partyName);
    } else {
      window.open(`/party/${partyId}/data/`, '_blank');
    }
  };

  const checkBlueprint = async (compName) => {
    if (!compName) {
      setCompanyBlueprintInfo(null);
      return;
    }
    try {
      const res = await callEel('check_company_blueprint', compName);
      setCompanyBlueprintInfo(res);
    } catch (err) {
      console.error('Error checking blueprint:', err);
    }
  };

  const fetchCompanyBlueprints = async () => {
    try {
      const bMap = await callEel('list_company_blueprints');
      setBlueprintsMap(bMap || {});
    } catch (e) {
      console.error('Error fetching blueprints list:', e);
    }
  };

  const handleUploadCompanyBlueprint = async (compName, file) => {
    if (!compName || !compName.trim()) {
      showToast('Please enter or select a Company Name first!', 'warning');
      return;
    }
    if (!file) return;
    const formData = new FormData();
    formData.append('company', compName.trim());
    formData.append('file', file);
    showToast(`Uploading master blueprint for "${compName}"...`, 'info');
    try {
      const res = await fetch('/main-app/upload-company-template/', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(data.message || 'Blueprint uploaded successfully!', 'success');
        await checkBlueprint(compName);
        await fetchCompanyBlueprints();
      } else {
        showToast(data.error || 'Failed to upload blueprint', 'error');
      }
    } catch (err) {
      showToast('Upload error: ' + (err.message || err), 'error');
    }
  };

  const handleUploadDataXlsx = async (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    if (selectedCompany) {
      formData.append('company', selectedCompany);
    }
    showToast('Uploading, converting to DB & syncing SKU Catalog...', 'info');
    try {
      const response = await fetch('/main-app/upload-data/', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      if (data.status === 'success') {
        showToast(data.message || 'data.xlsx uploaded successfully!', 'success');
        if (data.catalog_sync && data.catalog_sync.status === 'success') {
          setCatalogSyncInfo(data.catalog_sync);
          showToast(`Synced ${data.catalog_sync.total || 0} items to Product & SKU Catalog!`, 'success');
        }
        if (Array.isArray(data.sheets) && data.sheets.length > 0) {
          setAvailableInputSheets(data.sheets);
        }
        await loadAvailableSheets();
        await loadExcelMappings();
      } else {
        showToast(data.error || 'Upload failed', 'error');
      }
    } catch (err) {
      showToast('Error uploading file: ' + (err.message || err), 'error');
    } finally {
      e.target.value = '';
    }
  };

  const handleSaveMapping = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!editingMapping) return;

    const mType = editingMapping.mapping_type || 'direct';
    const srcSheet = editingMapping.source_sheet || (availableInputSheets[0] || 'RING');
    let srcCol = (editingMapping.source_column || '').trim();
    const tgtSheet = editingMapping.target_sheet || (availableTargetSheets[0] || 'Cat-EngagementRings');
    const tgtCol = (editingMapping.target_column || '').trim();
    const defVal = (editingMapping.default_value || '').trim();

    if (mType === 'static' && !srcCol) {
      srcCol = '[DEFAULT]';
    }

    if (!srcSheet || !tgtSheet || !tgtCol) {
      showToast('Please fill all required sheet and target column fields', 'warning');
      return;
    }

    if (mType !== 'static' && !srcCol) {
      showToast('Please fill out the Source Column Name', 'warning');
      return;
    }

    if (mType === 'static' && !defVal) {
      showToast('Please specify the Constant Value for static mapping', 'warning');
      return;
    }

    const compName = editingMapping.company_name || 'All';
    try {
      await callEel(
        'save_excel_mapping',
        srcSheet,
        srcCol,
        tgtSheet,
        tgtCol,
        mType,
        defVal,
        editingMapping.id || null,
        compName
      );
      showToast(`Excel mapping saved for ${compName}!`, 'success');
      setShowMappingModal(false);
      setEditingMapping(null);
      await loadExcelMappings();
    } catch (err) {
      showToast('Error saving excel mapping', 'error');
    }
  };


  const handleDeleteMapping = async (mappingId) => {
    if (window.Swal) {
      const res = await Swal.fire({
        title: 'Delete Mapping Rule?',
        text: 'Are you sure you want to remove this column mapping rule?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#6b7280',
        confirmButtonText: 'Yes, delete'
      });
      if (!res.isConfirmed) return;
    }
    try {
      await callEel('delete_excel_mapping', mappingId);
      showToast('Mapping rule removed', 'info');
      await loadExcelMappings();
    } catch (err) {
      showToast('Error deleting mapping', 'error');
    }
  };

  const handleResetMappings = async () => {
    if (window.Swal) {
      const res = await Swal.fire({
        title: 'Reset All Mappings?',
        text: 'This will restore standard default mappings for active data.xlsx sheets.',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#6366f1',
        cancelButtonColor: '#6b7280',
        confirmButtonText: 'Yes, Reset Defaults'
      });
      if (!res.isConfirmed) return;
    }
    try {
      await callEel('reset_default_excel_mappings');
      showToast('Default mappings restored!', 'success');
      await loadExcelMappings();
    } catch (err) {
      showToast('Error resetting defaults', 'error');
    }
  };


  
  // HTML Templates & Live Preview State
  const [htmlTemplates, setHtmlTemplates] = useState([]);
  const [selectedHtmlCompany, setSelectedHtmlCompany] = useState('');
  const [selectedHtmlCategory, setSelectedHtmlCategory] = useState('');
  const [selectedHtmlSubcategory, setSelectedHtmlSubcategory] = useState('Default');
  const [currentHtmlText, setCurrentHtmlText] = useState('');
  const [currentHtmlTemplateId, setCurrentHtmlTemplateId] = useState(null);
  const [isSavingHtml, setIsSavingHtml] = useState(false);

  const [showLivePreview, setShowLivePreview] = useState(true);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewDataMode, setPreviewDataMode] = useState('raw'); // 'raw' | 'sample'
  const [previewDeviceMode, setPreviewDeviceMode] = useState('desktop'); // 'desktop' | 'mobile'
  const [isVisualEditing, setIsVisualEditing] = useState(false);
  const [isPreviewDetached, setIsPreviewDetached] = useState(false);
  const detachedWindowRef = useRef(null);

  const updateDetachedWindowContent = (win, htmlText, dataMode, visualEditing, deviceMode = 'desktop') => {
    if (!win || win.closed) return;
    try {
      const renderedHtml = renderLivePreviewHtml(htmlText, dataMode, visualEditing);
      
      // If detached window is already rendered for the SAME deviceMode, update srcdoc dynamically
      if (win.document && win.__renderedDeviceMode === deviceMode && win.document.getElementById('livePreviewIframe')) {
        const frame = win.document.getElementById('livePreviewIframe');
        if (frame) {
          frame.srcdoc = renderedHtml;
          return;
        }
      }

      // Record the active deviceMode on pop-out window instance
      win.__renderedDeviceMode = deviceMode;

      win.document.open();
      if (deviceMode === 'mobile') {
        win.document.write(`
          <!DOCTYPE html>
          <html>
            <head>
              <title>Live Listing Preview - Mobile View (Detached)</title>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
              <style>
                * { box-sizing: border-box; }
                body, html { margin: 0; padding: 0; width: 100%; height: 100%; background: #0b0f19; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #e2e8f0; overflow: hidden; display: flex; flex-direction: column; }
                .toolbar { height: 48px; background: #111827; border-bottom: 1px solid #1f2937; display: flex; align-items: center; justify-content: space-between; padding: 0 16px; flex-shrink: 0; }
                .title { font-size: 13px; font-weight: 700; color: #a5b4fc; display: flex; align-items: center; gap: 8px; }
                .controls { display: flex; align-items: center; gap: 10px; }
                .select-btn { background: #1f2937; color: #cbd5e1; border: 1px solid #374151; padding: 5px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; outline: none; cursor: pointer; }
                .stage { flex: 1; overflow: auto; display: flex; justify-content: center; align-items: flex-start; padding: 25px 15px; background: radial-gradient(circle at center, #1e1b4b 0%, #090d16 100%); }
                .phone-container { width: 390px; height: 760px; max-height: 92vh; background: #000000; border-radius: 44px; border: 12px solid #1f2937; box-shadow: 0 25px 60px -15px rgba(0,0,0,0.8), 0 0 30px rgba(99,102,241,0.2); position: relative; display: flex; flex-direction: column; overflow: hidden; transition: all 0.3s ease; }
                .phone-notch { width: 130px; height: 22px; background: #1f2937; border-bottom-left-radius: 14px; border-bottom-right-radius: 14px; margin: 0 auto; display: flex; align-items: center; justify-content: center; gap: 8px; flex-shrink: 0; z-index: 10; }
                .camera { width: 8px; height: 8px; background: #090d16; border-radius: 50%; }
                .speaker { width: 40px; height: 4px; background: #374151; border-radius: 2px; }
                .phone-screen { flex: 1; width: 100%; background: #ffffff; overflow: hidden; display: flex; flex-direction: column; }
                iframe { width: 100%; height: 100%; border: 0; flex: 1; }
              </style>
            </head>
            <body>
              <div class="toolbar">
                <div class="title">
                  <i class="fa-solid fa-mobile-screen-button"></i>
                  <span>Mobile Viewport Preview</span>
                </div>
                <div class="controls">
                  <label style="font-size: 11px; color: #94a3b8; font-weight: 600;">Device Model:</label>
                  <select id="deviceSelect" class="select-btn" onchange="
                    const container = document.querySelector('.phone-container');
                    if (this.value === 'iphone') { container.style.width = '390px'; container.style.height = '760px'; }
                    else if (this.value === 'galaxy') { container.style.width = '412px'; container.style.height = '780px'; }
                    else if (this.value === 'compact') { container.style.width = '360px'; container.style.height = '680px'; }
                    else if (this.value === 'tablet') { container.style.width = '768px'; container.style.height = '900px'; }
                  ">
                    <option value="iphone">iPhone 14/15 (390px)</option>
                    <option value="galaxy">Samsung Galaxy (412px)</option>
                    <option value="compact">Compact Phone (360px)</option>
                    <option value="tablet">iPad / Tablet (768px)</option>
                  </select>
                </div>
              </div>
              <div class="stage">
                <div class="phone-container">
                  <div class="phone-notch">
                    <div class="speaker"></div>
                    <div class="camera"></div>
                  </div>
                  <div class="phone-screen">
                    <iframe id="livePreviewIframe" title="Mobile Preview" srcdoc="${renderedHtml.replace(/"/g, '&quot;')}" sandbox="allow-scripts allow-same-origin"></iframe>
                  </div>
                </div>
              </div>
            </body>
          </html>
        `);
      } else {
        win.document.write(`
          <!DOCTYPE html>
          <html>
            <head>
              <title>Live Listing Preview - Desktop View (Detached)</title>
              <meta charset="utf-8">
              <style>
                body, html { margin: 0; padding: 0; width: 100%; height: 100%; overflow: auto; background: #ffffff; }
                iframe { width: 100%; height: 100%; border: 0; }
              </style>
            </head>
            <body>
              <iframe id="livePreviewIframe" title="Desktop Preview" srcdoc="${renderedHtml.replace(/"/g, '&quot;')}" sandbox="allow-scripts allow-same-origin"></iframe>
            </body>
          </html>
        `);
      }
      win.document.close();
    } catch (e) {
      console.error("Error updating detached window:", e);
    }
  };

  const handleOpenDetachedWindow = () => {
    if (detachedWindowRef.current && !detachedWindowRef.current.closed) {
      detachedWindowRef.current.focus();
      return;
    }

    const popWin = window.open('', 'LiveHTMLPreviewWindow', 'width=1280,height=900,resizable=yes,scrollbars=yes');
    if (popWin) {
      detachedWindowRef.current = popWin;
      setIsPreviewDetached(true);
      updateDetachedWindowContent(popWin, currentHtmlText, previewDataMode, isVisualEditing, previewDeviceMode);
      showToast('Live preview detached into separate window!', 'success');

      const checkClosed = setInterval(() => {
        if (popWin.closed) {
          clearInterval(checkClosed);
          setIsPreviewDetached(false);
          detachedWindowRef.current = null;
        }
      }, 800);
    } else {
      showToast('Popup blocked! Please allow popups for detached preview window.', 'error');
    }
  };

  const handleCloseDetachedWindow = () => {
    if (detachedWindowRef.current && !detachedWindowRef.current.closed) {
      detachedWindowRef.current.close();
    }
    detachedWindowRef.current = null;
    setIsPreviewDetached(false);
    showToast('Preview window docked back into application.', 'info');
  };

  useEffect(() => {
    if (detachedWindowRef.current && !detachedWindowRef.current.closed) {
      updateDetachedWindowContent(detachedWindowRef.current, currentHtmlText, previewDataMode, isVisualEditing, previewDeviceMode);
    }
  }, [currentHtmlText, previewDataMode, isVisualEditing, previewDeviceMode]);
  const [htmlSelectionRange, setHtmlSelectionRange] = useState({ start: 0, end: 0 });
  const [titleSelectionRange, setTitleSelectionRange] = useState({ start: 0, end: 0 });
  const titleTextareaRef = useRef(null);
  const [previewSelectedText, setPreviewSelectedText] = useState('');
  const [inspectedElement, setInspectedElement] = useState(null);
  const [replacementTextInput, setReplacementTextInput] = useState('');

  useEffect(() => {
    if (previewSelectedText) {
      setReplacementTextInput(previewSelectedText);
    } else {
      setReplacementTextInput('');
    }
  }, [previewSelectedText]);

  const formatTag = (name) => {
    if (!name) return '';
    const clean = name.replace(/[{}]/g, '').trim();
    return `{${clean}}`;
  };

  const replaceHtmlContentText = (rawHtml, targetText, replacementText) => {
    if (!rawHtml || !targetText) return { success: false, newHtml: rawHtml };
    
    const cleanTarget = targetText.trim();
    const cleanReplacement = String(replacementText).trim();
    if (!cleanTarget || !cleanReplacement) return { success: false, newHtml: rawHtml };

    const targetsToTry = [
      cleanTarget,
      cleanTarget.replace(/:$/, '').trim(),
      cleanTarget.replace(/\s+/g, ' ').trim()
    ];

    for (let target of targetsToTry) {
      if (!target) continue;

      // 1. Direct exact substring match
      if (rawHtml.includes(target)) {
        return { success: true, newHtml: rawHtml.replace(target, cleanReplacement) };
      }

      // 2. Case-insensitive exact match
      const lowerHtml = rawHtml.toLowerCase();
      const lowerTarget = target.toLowerCase();
      const exactIdx = lowerHtml.indexOf(lowerTarget);
      if (exactIdx !== -1) {
        const updated = rawHtml.substring(0, exactIdx) + cleanReplacement + rawHtml.substring(exactIdx + target.length);
        return { success: true, newHtml: updated };
      }

      // 3. Tag-Aware & Whitespace-Insensitive Regex Match (matches across inner HTML tags like <div class="spRgt">)
      try {
        const words = target.split(/\s+/).map(w => w.replace(/[-[\]{}()*+?.,\\^$|#]/g, '\\$&'));
        const regexPattern = words.join('(?:\\s*<[^>]+>\\s*|\\s+)');
        const re = new RegExp(regexPattern, 'i');
        if (re.test(rawHtml)) {
          return { success: true, newHtml: rawHtml.replace(re, cleanReplacement) };
        }
      } catch (e) {
        console.warn('Tag-aware regex replace error:', e);
      }

      // 4. HTML Entity & Special Char match (&nbsp;, &amp;)
      try {
        const entityPattern = target
          .replace(/&/g, '(?:&|&amp;)')
          .split(/\s+/)
          .map(w => w.replace(/[-[\]{}()*+?.,\\^$|#]/g, '\\$&'))
          .join('(?:\\s+|&nbsp;)+');
        const reEntity = new RegExp(entityPattern, 'i');
        if (reEntity.test(rawHtml)) {
          return { success: true, newHtml: rawHtml.replace(reEntity, cleanReplacement) };
        }
      } catch (e) {
        console.warn('Entity regex replace error:', e);
      }
    }

    return { success: false, newHtml: rawHtml };
  };

  const handleTitleTextareaSelect = (e) => {
    if (e && e.target) {
      setTitleSelectionRange({
        start: e.target.selectionStart,
        end: e.target.selectionEnd
      });
    }
  };

  const handleInsertTagToTitleTemplate = (tagName) => {
    const cleanTag = formatTag(tagName);
    const textarea = titleTextareaRef.current;

    setEditingTemplate(prev => {
      if (!prev) return null;
      const currentText = (prev.template_text || '').replace(/\{\{/g, '{').replace(/\}\}/g, '}');
      
      let start = titleSelectionRange.start;
      let end = titleSelectionRange.end;

      if (textarea && textarea.selectionStart !== undefined && textarea.selectionEnd !== undefined && textarea.selectionStart !== textarea.selectionEnd) {
        start = textarea.selectionStart;
        end = textarea.selectionEnd;
      }

      if ((start === 0 && end === 0) && textarea) {
        start = textarea.selectionStart || currentText.length;
        end = textarea.selectionEnd || currentText.length;
      }

      const updatedText = currentText.substring(0, start) + cleanTag + currentText.substring(end);
      const replaced = start !== end;

      setTimeout(() => {
        if (textarea) {
          textarea.focus();
          const newPos = start + cleanTag.length;
          textarea.setSelectionRange(newPos, newPos);
          setTitleSelectionRange({ start: newPos, end: newPos });
        }
      }, 0);

      showToast(replaced ? `Replaced selection with ${cleanTag}` : `Inserted ${cleanTag}`, 'info');

      return {
        ...prev,
        template_text: updatedText
      };
    });
  };

  const previewIframeRef = useRef(null);

  const postToIframe = (msg) => {
    if (previewIframeRef.current && previewIframeRef.current.contentWindow) {
      previewIframeRef.current.contentWindow.postMessage(msg, '*');
    }
  };

  const handleUpdateInspectedElement = (field, value) => {
    setInspectedElement(prev => prev ? ({ ...prev, [field]: value }) : null);

    if (currentHtmlText && inspectedElement && inspectedElement.path && inspectedElement.path.length > 0) {
      try {
        const parser = new DOMParser();
        const doc = parser.parseFromString(currentHtmlText, 'text/html');
        let target = doc.body;
        for (let idx of inspectedElement.path) {
          if (target && target.children && target.children[idx]) {
            target = target.children[idx];
          } else {
            target = null;
            break;
          }
        }

        if (target) {
          if (field === 'innerText') {
            target.innerText = value;
          } else if (field === 'className') {
            target.className = value;
          } else if (field === 'outerHTML') {
            try {
              const temp = doc.createElement('div');
              temp.innerHTML = value;
              if (temp.firstElementChild) {
                target.replaceWith(temp.firstElementChild);
              }
            } catch(e) {
              console.error('OuterHTML parse error:', e);
            }
          }
          setCurrentHtmlText(doc.body.innerHTML);
        }
      } catch(err) {
        console.error('DOMParser update error:', err);
      }
    }

    postToIframe({ type: 'EXEC_INSPECT_UPDATE', field, value });
  };

  const handleDeleteInspectedElement = () => {
    if (!inspectedElement) return;

    if (currentHtmlText && inspectedElement.path && inspectedElement.path.length > 0) {
      try {
        const parser = new DOMParser();
        const doc = parser.parseFromString(currentHtmlText, 'text/html');
        let target = doc.body;
        for (let idx of inspectedElement.path) {
          if (target && target.children && target.children[idx]) {
            target = target.children[idx];
          } else {
            target = null;
            break;
          }
        }

        if (target) {
          target.remove();
          setCurrentHtmlText(doc.body.innerHTML);
        }
      } catch(err) {
        console.error('DOMParser delete error:', err);
      }
    }

    setInspectedElement(null);
    postToIframe({ type: 'EXEC_INSPECT_DELETE' });
  };

  const [editingPolicy, setEditingPolicy] = useState(null);
  const [editingTemplate, setEditingTemplate] = useState(null);
  
  const [newProductName, setNewProductName] = useState('');
  const [newPlaceholderName, setNewPlaceholderName] = useState('');
  const [newCatName, setNewCatName] = useState('');
  const [newColName, setNewColName] = useState('');
  const [newColCat, setNewColCat] = useState('');
  const [newSubcatName, setNewSubcatName] = useState('');
  const [newSubcatCat, setNewSubcatCat] = useState('');
  
  const [showAddPlaceholderInput, setShowAddPlaceholderInput] = useState(false);
  const [showAddCatModal, setShowAddCatModal] = useState(false);
  const [showAddColModal, setShowAddColModal] = useState(false);
  const [showAddSubcatModal, setShowAddSubcatModal] = useState(false);

  // Textarea Refs
  const templateTextareaRef = useRef(null);
  const htmlEditorTextareaRef = useRef(null);

  // Filters for title templates & dynamic cascading auto-filter
  const [templateMetalFilter, setTemplateMetalFilter] = useState('all');
  const [templateCatFilter, setTemplateCatFilter] = useState('all');
  const [templateSettingFilter, setTemplateSettingFilter] = useState('all');
  const [templateCompanyFilter, setTemplateCompanyFilter] = useState('all');
  const [autoFilterEmpty, setAutoFilterEmpty] = useState(true);

  // Admin Mode & Delete Protection State
  const [adminPassword, setAdminPassword] = useState('0000');
  const [isAdminMode, setIsAdminMode] = useState(false);
  const [showAdminPassModal, setShowAdminPassModal] = useState(false);
  const [adminPassInput, setAdminPassInput] = useState('');
  const [editModalConfig, setEditModalConfig] = useState(null);
  const [showSaveHtmlPassModal, setShowSaveHtmlPassModal] = useState(false);
  const [saveHtmlPassInput, setSaveHtmlPassInput] = useState('');

  const [showChangePassModal, setShowChangePassModal] = useState(false);
  const [changePassCurrent, setChangePassCurrent] = useState('');
  const [changePassNew, setChangePassNew] = useState('');
  const [changePassConfirm, setChangePassConfirm] = useState('');

  // Resizable Sidebar State & Handlers
  const [sidebarWidth, setSidebarWidth] = useState(285);
  const [isResizingSidebar, setIsResizingSidebar] = useState(false);

  // Sidebar Visibility State (Show / Hide toggle)
  const [isSidebarVisible, setIsSidebarVisible] = useState(() => {
    const saved = localStorage.getItem('app_sidebar_visible');
    return saved !== null ? saved === 'true' : true;
  });

  const toggleSidebar = () => {
    const nextState = !isSidebarVisible;
    setIsSidebarVisible(nextState);
    localStorage.setItem('app_sidebar_visible', nextState ? 'true' : 'false');
  };

  // Global Keyboard Shortcut Listener (Esc Key to Toggle Sidebar)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        // Only toggle if no modal overlays are active
        const hasOpenModal = showAddCatModal || showAddSubcatModal || showAddColModal || 
                             showAdminPassModal || showSaveHtmlPassModal || showChangePassModal || 
                             showMappingModal || editModalConfig || showPreviewModal;
        if (!hasOpenModal) {
          toggleSidebar();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSidebarVisible, showAddCatModal, showAddSubcatModal, showAddColModal, showAdminPassModal, showSaveHtmlPassModal, showChangePassModal, showMappingModal, editModalConfig, showPreviewModal]);

  const handleMouseDownResizer = (e) => {
    e.preventDefault();
    setIsResizingSidebar(true);
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizingSidebar) return;
      const newWidth = Math.min(Math.max(e.clientX - 16, 200), 520);
      setSidebarWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizingSidebar(false);
    };

    if (isResizingSidebar) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizingSidebar]);

  // Resizable Editor & Preview Layout States & Refs
  const [editorSplitRatio, setEditorSplitRatio] = useState(null); // null = default auto-height for tags, number = custom user drag ratio
  const [isResizingEditorSplit, setIsResizingEditorSplit] = useState(false);
  const leftPaneContainerRef = useRef(null);

  const [paneSplitRatio, setPaneSplitRatio] = useState(50); // 50% left pane, 50% right preview
  const [isResizingPaneSplit, setIsResizingPaneSplit] = useState(false);
  const mainGridContainerRef = useRef(null);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isResizingEditorSplit && leftPaneContainerRef.current) {
        const rect = leftPaneContainerRef.current.getBoundingClientRect();
        const offsetY = e.clientY - rect.top;
        const newRatio = Math.min(Math.max((offsetY / rect.height) * 100, 15), 85);
        setEditorSplitRatio(newRatio);
      }
      if (isResizingPaneSplit && mainGridContainerRef.current) {
        const rect = mainGridContainerRef.current.getBoundingClientRect();
        const offsetX = e.clientX - rect.left;
        const newRatio = Math.min(Math.max((offsetX / rect.width) * 100, 20), 80);
        setPaneSplitRatio(newRatio);
      }
    };

    const handleMouseUp = () => {
      if (isResizingEditorSplit) setIsResizingEditorSplit(false);
      if (isResizingPaneSplit) setIsResizingPaneSplit(false);
    };

    if (isResizingEditorSplit || isResizingPaneSplit) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizingEditorSplit, isResizingPaneSplit]);

  // Find & Replace State for HTML Editor
  const [showFindReplaceBar, setShowFindReplaceBar] = useState(false);
  const [findSearchText, setFindSearchText] = useState('');
  const [replaceWithText, setReplaceWithText] = useState('');
  const [isCaseSensitive, setIsCaseSensitive] = useState(false);

  // Compute total matches in currentHtmlText
  const findMatchCount = useMemo(() => {
    if (!findSearchText || !currentHtmlText) return 0;
    try {
      const flags = isCaseSensitive ? 'g' : 'gi';
      const escaped = findSearchText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(escaped, flags);
      const matches = currentHtmlText.match(regex);
      return matches ? matches.length : 0;
    } catch (e) {
      return 0;
    }
  }, [findSearchText, currentHtmlText, isCaseSensitive]);

  // Customizable Navigation Sidebar Labels State
  const [navLabels, setNavLabels] = useState(() => {
    const saved = localStorage.getItem('app_nav_labels');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) {}
    }
    return {
      generator: 'Data Generator Master',
      html_master: 'HTML App (Modifier) Master',
      database: 'Database Manager Master',
      mapping: 'Excel Mapping Master',
      settings: 'System Info Master'
    };
  });

  const handleUpdateNavLabel = (key, value) => {
    const updated = { ...navLabels, [key]: value };
    setNavLabels(updated);
  };

  const handleSaveNavLabels = () => {
    localStorage.setItem('app_nav_labels', JSON.stringify(navLabels));
    showToast('Navigation sidebar titles saved successfully!', 'success');
  };

  const handleResetNavLabels = () => {
    const defaults = {
      generator: 'Data Generator Master',
      html_master: 'HTML App (Modifier) Master',
      database: 'Database Manager Master',
      mapping: 'Excel Mapping Master',
      settings: 'System Info Master'
    };
    setNavLabels(defaults);
    localStorage.setItem('app_nav_labels', JSON.stringify(defaults));
    showToast('Navigation labels reset to defaults!', 'info');
  };

  // Sub-mode toggle for HTML App tab: 'integrated' | 'standalone_html_app'
  const [htmlAppMode, setHtmlAppMode] = useState('integrated');

  // Replace Next Occurrence
  const handleReplaceNext = () => {
    if (!findSearchText) {
      showToast('Please enter text to find', 'warning');
      return;
    }
    if (!currentHtmlText) return;

    try {
      const flags = isCaseSensitive ? '' : 'i';
      const escaped = findSearchText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(escaped, flags);
      if (regex.test(currentHtmlText)) {
        const newHtml = currentHtmlText.replace(regex, replaceWithText);
        setCurrentHtmlText(newHtml);
        showToast(`Replaced 1 occurrence of "${findSearchText}"`, 'success');
      } else {
        showToast(`No match found for "${findSearchText}"`, 'info');
      }
    } catch (err) {
      showToast(`Replace error: ${err.message}`, 'error');
    }
  };

  // Replace All Occurrences
  const handleReplaceAll = () => {
    if (!findSearchText) {
      showToast('Please enter text to find', 'warning');
      return;
    }
    if (!currentHtmlText) return;

    try {
      const flags = isCaseSensitive ? 'g' : 'gi';
      const escaped = findSearchText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(escaped, flags);
      const matches = currentHtmlText.match(regex);
      const count = matches ? matches.length : 0;

      if (count > 0) {
        const newHtml = currentHtmlText.replace(regex, replaceWithText);
        setCurrentHtmlText(newHtml);
        showToast(`Replaced all ${count} occurrence(s) of "${findSearchText}" with "${replaceWithText}"!`, 'success');
      } else {
        showToast(`No matches found for "${findSearchText}"`, 'info');
      }
    } catch (err) {
      showToast(`Replace All error: ${err.message}`, 'error');
    }
  };

  // HTML Templates Excel Import & Export Handlers
  const fileInputRefHtmlExcel = useRef(null);

  const downloadB64File = (b64Data, filename, contentType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') => {
    try {
      const link = document.createElement('a');
      link.href = `data:${contentType};base64,${b64Data}`;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error('File download error:', err);
    }
  };

  const handleExportHtmlTemplatesToExcel = async () => {
    try {
      const res = await callEel('export_html_templates_to_excel', selectedHtmlCompany || 'all');
      if (res && res.status === 'success' && res.file_b64) {
        downloadB64File(res.file_b64, res.filename || 'HTML_Templates.xlsx');
        showToast(res.message || 'Exported HTML templates to Excel!', 'success');
      } else {
        showToast(res?.message || 'Export failed', 'warning');
      }
    } catch (err) {
      showToast(`Export error: ${err.message}`, 'error');
    }
  };

  const handleDownloadSampleHtmlExcel = async () => {
    try {
      const res = await callEel('get_sample_html_excel_data');
      if (res && res.file_b64) {
        downloadB64File(res.file_b64, res.filename || 'Sample_HTML_Templates.xlsx');
        showToast('Downloaded sample HTML templates Excel file!', 'info');
      }
    } catch (err) {
      showToast(`Sample download error: ${err.message}`, 'error');
    }
  };

  const handleImportHtmlExcelChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const b64 = event.target.result;
        showToast('Processing Excel file import...', 'info');
        const res = await callEel('import_html_templates_from_excel', b64);
        if (res && res.status === 'success') {
          showToast(res.message, 'success');
          await loadDatabaseItems();
        } else {
          showToast(res?.message || 'Import failed', 'error');
        }
      } catch (err) {
        showToast(`Import error: ${err.message}`, 'error');
      } finally {
        if (fileInputRefHtmlExcel.current) {
          fileInputRefHtmlExcel.current.value = '';
        }
      }
    };
    reader.readAsDataURL(file);
  };

  useEffect(() => {
    callEel('get_admin_password').then(pwd => {
      if (pwd) setAdminPassword(pwd);
    }).catch(err => console.error(err));

    window.notify_main_updated = (updatedHtml) => {
      if (updatedHtml && updatedHtml !== 'ERROR' && updatedHtml !== 'EMPTY_INPUT' && updatedHtml !== 'NO_MARKER') {
        setCurrentHtmlText(updatedHtml);
        showToast('HTML code modified from Quick Widget!', 'success');
      }
    };
    if (window.eel) {
      try {
        window.eel.expose(window.notify_main_updated, 'notify_main_updated');
      } catch (e) {}
    }
  }, []);

  const handleLogoDoubleClick = () => {
    if (isAdminMode) {
      setIsAdminMode(false);
      showToast('Admin Mode Deactivated. Delete options locked.', 'info');
    } else {
      setAdminPassInput('');
      setShowAdminPassModal(true);
    }
  };

  const handleAdminPassSubmit = (e) => {
    e.preventDefault();
    if (adminPassInput.trim() === adminPassword) {
      setIsAdminMode(true);
      setShowAdminPassModal(false);
      setAdminPassInput('');
      showToast('Admin Mode Activated! Delete options unlocked.', 'success');
    } else {
      showToast('Incorrect Admin Password!', 'error');
    }
  };

  const handleChangePasswordSubmit = async (e) => {
    e.preventDefault();
    if (changePassCurrent.trim() !== adminPassword) {
      showToast('Current password is incorrect!', 'error');
      return;
    }
    if (!changePassNew.trim()) {
      showToast('New password cannot be empty!', 'warning');
      return;
    }
    if (changePassNew.trim() !== changePassConfirm.trim()) {
      showToast('New passwords do not match!', 'error');
      return;
    }
    try {
      await callEel('update_admin_password', changePassNew.trim());
      setAdminPassword(changePassNew.trim());
      setShowChangePassModal(false);
      setChangePassCurrent('');
      setChangePassNew('');
      setChangePassConfirm('');
      showToast('Admin Password updated successfully!', 'success');
    } catch (err) {
      showToast('Failed to update admin password', 'error');
    }
  };

  // Toast state
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'info') => {
    setToast({ message, type, id: Date.now() });
    setTimeout(() => setToast(null), 4000);
  };

  // Helper to sort list placing 'Default' / 'default' at index 0 (top of menu)
  const sortWithDefaultFirst = (list) => {
    if (!Array.isArray(list)) return [];
    return [...list].sort((a, b) => {
      const nameA = (typeof a === 'string' ? a : (a.name || '')).toLowerCase();
      const nameB = (typeof b === 'string' ? b : (b.name || '')).toLowerCase();
      if (nameA === 'default') return -1;
      if (nameB === 'default') return 1;
      return nameA.localeCompare(nameB);
    });
  };

  // Category Dropdown: ALWAYS show ALL Categories (Default always on top)
  const availableCategories = useMemo(() => {
    return sortWithDefaultFirst(dbCategories);
  }, [dbCategories]);

  // Helper: Filter setting columns by category scope
  const getSettingColumnsForCategory = (categoryName, allColumns, templatesList = []) => {
    if (!categoryName || categoryName === 'all') return sortWithDefaultFirst(allColumns);
    const targetCatLower = categoryName.toLowerCase();
    const colsWithTemplates = new Set(
      (templatesList || [])
        .filter(t => t.product_category && t.product_category.toLowerCase() === targetCatLower)
        .map(t => t.setting_column.toLowerCase())
    );
    colsWithTemplates.add('default');
    colsWithTemplates.add('title');

    const filtered = (allColumns || []).filter(col => {
      const colCat = (col.category || '').toLowerCase();
      const colName = col.name.toLowerCase();
      if (colName === 'default' || colName === 'title') return true;
      if (colCat && colCat !== 'all' && colCat !== 'default') {
        return colCat === targetCatLower;
      }
      return colsWithTemplates.has(colName);
    });
    return sortWithDefaultFirst(filtered);
  };

  // Dynamic Cascading Auto-Filter: Computed setting columns with templates for selected Category (Default always on top)
  const availableSettingColumns = useMemo(() => {
    return getSettingColumnsForCategory(templateCatFilter, dbSettingColumns, templates);
  }, [dbSettingColumns, templates, templateCatFilter, autoFilterEmpty]);

  // Listen for text selections & visual element edits from the Live Preview iframe
  useEffect(() => {
    const handleMessage = (e) => {
      if (e.data && e.data.type === 'HTML_PREVIEW_SELECTION') {
        const text = e.data.selectedText;
        if (text && text.trim()) {
          setPreviewSelectedText(text.trim());
        }
      } else if (e.data && e.data.type === 'LIVE_ELEMENT_EDIT') {
        if (e.data.updatedHtml) {
          setCurrentHtmlText(e.data.updatedHtml);
        }
      } else if (e.data && e.data.type === 'INSPECT_ELEMENT') {
        setInspectedElement(e.data.elementInfo || null);
      }
    };
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [currentHtmlText]);

  // Load initial companies & products
  const reloadCompaniesAndProducts = async () => {
    try {
      const compList = await callEel('get_company_list');
      if (Array.isArray(compList)) {
        setCompanies(compList);
        if (!selectedHtmlCompany && compList.length > 0) {
          setSelectedHtmlCompany(compList[0]);
        }
      }
      
      const prodList = await callEel('get_product_list');
      if (Array.isArray(prodList)) setProducts(prodList);
    } catch (err) {
      showToast('Failed to load companies/products from database', 'error');
    }
  };

  const loadPlaceholders = async () => {
    try {
      const pList = await callEel('get_all_placeholders');
      if (Array.isArray(pList)) setPlaceholders(pList);
    } catch (err) {
      console.error('Error loading placeholders:', err);
    }
  };

  const loadSubcategories = async (catName) => {
    try {
      const targetCat = catName || selectedHtmlCategory || '';
      const subs = await callEel('get_all_subcategories', targetCat);
      if (Array.isArray(subs)) setDbSubcategories(subs);
    } catch (err) {
      console.error('Error loading subcategories:', err);
    }
  };

  useEffect(() => {
    if (selectedHtmlCategory) {
      setSelectedHtmlSubcategory('Default');
      loadSubcategories(selectedHtmlCategory);
    }
  }, [selectedHtmlCategory]);

  const loadCategoriesAndColumns = async () => {
    try {
      const cats = await callEel('get_all_categories');
      if (Array.isArray(cats)) {
        setDbCategories(cats);
        if (cats.length > 0 && (!selectedHtmlCategory || selectedHtmlCategory === 'default')) {
          setSelectedHtmlCategory(cats[0].name);
        }
      }

      const cols = await callEel('get_all_setting_columns');
      if (Array.isArray(cols)) setDbSettingColumns(cols);

      await loadSubcategories();
    } catch (err) {
      console.error('Error loading categories/columns:', err);
    }
  };

  const loadCompanyHtmlTemplates = async () => {
    try {
      const tmpls = await callEel('get_all_company_html_templates');
      if (Array.isArray(tmpls)) setHtmlTemplates(tmpls);
    } catch (err) {
      console.error('Error loading HTML templates:', err);
    }
  };

  useEffect(() => {
    reloadCompaniesAndProducts();
    loadPlaceholders();
    loadCategoriesAndColumns();
    loadCompanyHtmlTemplates();
  }, []);

  // Sync active HTML template string when selected company, category, or subcategory changes (EXACT MATCH ONLY!)
  useEffect(() => {
    if (!selectedHtmlCompany) return;
    setPreviewSelectedText('');

    const comp = (selectedHtmlCompany || '').toLowerCase();
    const cat = (selectedHtmlCategory || '').toLowerCase();
    const subcat = (selectedHtmlSubcategory || 'default').toLowerCase();

    // 1. Exact match (company + category + subcategory)
    let exactMatch = htmlTemplates.find(
      h => (h.company_name || '').toLowerCase() === comp &&
           (h.category || '').toLowerCase() === cat &&
           ((h.subcategory || 'default').toLowerCase() === subcat)
    );

    if (exactMatch) {
      setCurrentHtmlText(exactMatch.html_template);
      setCurrentHtmlTemplateId(exactMatch.id);
    } else {
      // 2. Subcategory / Category fallback to starter HTML code (set template ID to null so saving creates a NEW row without overwriting Default!)
      let fallbackMatch = htmlTemplates.find(
        h => (h.company_name || '').toLowerCase() === comp &&
             (h.category || '').toLowerCase() === cat &&
             ((h.subcategory || 'default').toLowerCase() === 'default' || !h.subcategory)
      );
      if (!fallbackMatch) {
        fallbackMatch = htmlTemplates.find(
          h => (h.company_name || '').toLowerCase() === comp &&
               ((h.category || 'default').toLowerCase() === 'default' || !h.category)
        );
      }

      if (fallbackMatch) {
        setCurrentHtmlText(fallbackMatch.html_template);
      } else {
        setCurrentHtmlText('');
      }
      // CRITICAL: ID is null when saving a new subcategory template so Default is never overwritten!
      setCurrentHtmlTemplateId(null);
    }
  }, [selectedHtmlCompany, selectedHtmlCategory, selectedHtmlSubcategory, htmlTemplates]);

  // Load Database Items when Database tab is opened
  const loadDatabaseItems = async () => {
    try {
      const pols = await callEel('get_all_company_policies');
      if (Array.isArray(pols)) setPolicies(pols);

      const tmpls = await callEel('get_all_title_templates');
      if (Array.isArray(tmpls)) setTemplates(tmpls);

      await loadPlaceholders();
      await loadCategoriesAndColumns();
      await loadCompanyHtmlTemplates();
      await fetchCompanyBlueprints();
    } catch (err) {
      showToast('Error loading database contents', 'error');
    }
  };

  useEffect(() => {
    loadAvailableSheets();
    fetchCompanyBlueprints();
  }, []);

  useEffect(() => {
    if (activeTab === 'database' || activeTab === 'html_master') {
      loadDatabaseItems();
    } else if (activeTab === 'mapping') {
      loadExcelMappings();
    }
  }, [activeTab]);



  // Handlers for Selects & Toggles
  const handleCompanyChange = async (e) => {
    const val = e.target.value;
    setSelectedCompany(val);
    await callEel('get_company_name', val);
    await checkBlueprint(val);
    showToast(`Company set to: ${val || 'None'}`, 'info');
  };

  const handleProductChange = async (e) => {
    const val = e.target.value;
    setSelectedProduct(val);
    await callEel('get_product_name', val);
    showToast(`Product set to: ${val || 'None'}`, 'info');
  };

  const handleColorVariationToggle = async () => {
    const newState = !colorVariation;
    setColorVariation(newState);
    await callEel('color_variation', newState);
    showToast(`Color Variation: ${newState ? 'ON' : 'OFF'}`, newState ? 'success' : 'info');
  };

  const handleGoldPurityToggle = async () => {
    const newState = !goldPurityVariation;
    setGoldPurityVariation(newState);
    await callEel('gold_purity_variation', newState);
    showToast(`Gold Purity Variation: ${newState ? 'ON' : 'OFF'}`, newState ? 'success' : 'info');
  };

  const handleProcessClick = async () => {
    if (!selectedCompany) {
      showToast('Please select a Company first!', 'warning');
      return;
    }

    setIsProcessing(true);
    setProcessStatus('Auto-processing all data.xlsx sheets & exporting...');

    try {
      const result = await callEel('app1');
      setProcessStatus(result || 'Multi-sheet process completed!');
      showToast('All data.xlsx sheets processed successfully!', 'success');

      // Auto trigger download of generated API-*.xlsx file
      const match = (result || '').match(/API-[\d\w-]+\.xlsx/i);
      if (match) {
        const exportFile = match[0];
        setLatestExportFilename(exportFile);
        const link = document.createElement('a');
        link.href = `/main-app/download-output/?file=${encodeURIComponent(exportFile)}`;
        link.download = exportFile;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showToast(`Auto-downloading: ${exportFile}`, 'info');
      }

      // Sync and retrieve updated Product & SKU Catalog details
      try {
        const catInfo = await callEel('get_catalog_sync_info');
        if (catInfo && catInfo.status === 'success') {
          setCatalogSyncInfo(catInfo);
          showToast(`Synced ${catInfo.total || 0} items to Product & SKU Catalog!`, 'success');
        }
      } catch (catErr) {
        console.error('Error fetching catalog sync info:', catErr);
      }
    } catch (err) {
      setProcessStatus('Error during processing');
      showToast('Processing failed: ' + (err.message || err), 'error');
    } finally {
      setIsProcessing(false);
    }
  };


  const handleClearExcel = async () => {
    setIsClearing(true);
    try {
      await callEel('clear_multiXlsx');
      setClearStatus(true);
      showToast('Multi_API.xlsx cleared!', 'success');
      setTimeout(() => setClearStatus(false), 2000);
    } catch (err) {
      showToast('Failed to clear Multi_API.xlsx', 'error');
    } finally {
      setIsClearing(false);
    }
  };

  // --- INTERACTIVE PLACEHOLDER INSERTION & REPLACEMENT ---
  const handleInsertPlaceholderTag = (tagName) => {
    if (!editingTemplate) return;
    
    const textarea = templateTextareaRef.current;
    const currentText = editingTemplate.template_text || '';

    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;

      const updatedText = currentText.substring(0, start) + tagName + currentText.substring(end);
      setEditingTemplate({ ...editingTemplate, template_text: updatedText });

      setTimeout(() => {
        textarea.focus();
        const newCursorPos = start + tagName.length;
        textarea.setSelectionRange(newCursorPos, newCursorPos);
      }, 0);

      const replaced = start !== end;
      showToast(replaced ? `Replaced selection with ${tagName}` : `Inserted ${tagName}`, 'info');
    } else {
      setEditingTemplate({ ...editingTemplate, template_text: currentText + ' ' + tagName });
    }
  };

  // Capture text selection in HTML code textarea
  const handleHtmlTextareaSelect = (e) => {
    setHtmlSelectionRange({
      start: e.target.selectionStart,
      end: e.target.selectionEnd
    });
  };

  // Replace highlighted selection (from Live Preview OR Textarea) with placeholder tag
  const handleInsertHtmlTag = (tagName) => {
    const formattedTag = formatTag(tagName);
    const currentText = currentHtmlText || '';

    // Priority 1: Text highlighted directly in Live Preview window!
    if (previewSelectedText) {
      const res = replaceHtmlContentText(currentText, previewSelectedText, formattedTag);
      if (res.success) {
        setCurrentHtmlText(res.newHtml);
        showToast(`Replaced "${previewSelectedText}" with ${formattedTag} in HTML code!`, 'success');
        setPreviewSelectedText('');
        setReplacementTextInput('');
        return;
      }
    }

    // Priority 2: Text highlighted in code textarea
    const textarea = htmlEditorTextareaRef.current;
    let start = htmlSelectionRange.start;
    let end = htmlSelectionRange.end;

    if (textarea && textarea.selectionStart !== textarea.selectionEnd) {
      start = textarea.selectionStart;
      end = textarea.selectionEnd;
    }

    const updatedText = currentText.substring(0, start) + formattedTag + currentText.substring(end);
    setCurrentHtmlText(updatedText);

    const replaced = start !== end;

    setTimeout(() => {
      if (textarea) {
        textarea.focus();
        const newPos = start + formattedTag.length;
        textarea.setSelectionRange(newPos, newPos);
        setHtmlSelectionRange({ start: newPos, end: newPos });
      }
    }, 0);

    showToast(replaced ? `Replaced selection with ${formattedTag}` : `Inserted ${formattedTag}`, 'info');
  };

  const handleSaveCompanyHtmlTemplate = () => {
    if (!selectedHtmlCompany) {
      showToast('Please select a company first', 'warning');
      return;
    }
    setSaveHtmlPassInput('');
    setShowSaveHtmlPassModal(true);
  };

  const executeSaveCompanyHtmlTemplate = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (saveHtmlPassInput.trim() !== adminPassword) {
      showToast('Incorrect password! HTML template not saved.', 'error');
      return;
    }
    setShowSaveHtmlPassModal(false);
    setSaveHtmlPassInput('');
    setIsSavingHtml(true);
    try {
      await callEel('save_company_html_template', selectedHtmlCompany, selectedHtmlCategory, selectedHtmlSubcategory, currentHtmlText, currentHtmlTemplateId);
      showToast(`HTML Template for ${selectedHtmlCompany} (${selectedHtmlCategory} / ${selectedHtmlSubcategory}) saved to DB!`, 'success');
      await loadCompanyHtmlTemplates();
    } catch (err) {
      showToast('Failed to save HTML template', 'error');
    } finally {
      setIsSavingHtml(false);
    }
  };

  const handleResetCompanyHtmlTemplate = async () => {
    try {
      const tmpls = await callEel('get_all_company_html_templates');
      if (Array.isArray(tmpls)) {
        setHtmlTemplates(tmpls);
        const match = tmpls.find(
          h => h.company_name.toLowerCase() === selectedHtmlCompany.toLowerCase() &&
               h.category.toLowerCase() === selectedHtmlCategory.toLowerCase() &&
               ((h.subcategory || 'default').toLowerCase() === (selectedHtmlSubcategory || 'default').toLowerCase())
        );
        if (match) {
          setCurrentHtmlText(match.html_template);
          setCurrentHtmlTemplateId(match.id);
        } else {
          setCurrentHtmlText('');
          setCurrentHtmlTemplateId(null);
        }
        showToast('Reset HTML content to fresh database version!', 'info');
      }
    } catch (err) {
      showToast('Failed to reset HTML template', 'error');
    }
  };

  const handleDeleteCompanyHtmlTemplate = async () => {
    if (!isAdminMode) {
      showToast('Admin Mode required to delete items! Double-click logo to unlock.', 'warning');
      return;
    }
    if (!currentHtmlTemplateId) {
      setCurrentHtmlText('');
      showToast('Cleared unsaved HTML editor content', 'info');
      return;
    }
    try {
      await callEel('delete_company_html_template', currentHtmlTemplateId);
      showToast('HTML template removed from DB', 'success');
      await loadCompanyHtmlTemplates();
    } catch (err) {
      showToast('Failed to delete HTML template', 'error');
    }
  };

  const handleReplaceSelectedPreviewText = (newTextValue) => {
    if (!previewSelectedText || newTextValue === undefined || newTextValue === null) return;
    if (!currentHtmlText) {
      showToast('No HTML code loaded to edit', 'warning');
      return;
    }

    const targetText = previewSelectedText.trim();
    const replacement = String(newTextValue).trim();

    if (!targetText || !replacement) return;

    const res = replaceHtmlContentText(currentHtmlText, targetText, replacement);

    if (res.success) {
      setCurrentHtmlText(res.newHtml);
      showToast(`Replaced "${targetText}" with "${replacement}" in HTML code!`, 'success');
      setPreviewSelectedText('');
      setReplacementTextInput('');
    } else {
      showToast(`Could not find "${targetText}" in HTML code`, 'warning');
    }
  };

  const handleAddPlaceholderToDb = async (e) => {
    e.preventDefault();
    if (!newPlaceholderName.trim()) return;
    try {
      await callEel('add_placeholder', newPlaceholderName.trim());
      showToast(`Added placeholder tag to database!`, 'success');
      setNewPlaceholderName('');
      setShowAddPlaceholderInput(false);
      await loadPlaceholders();
    } catch (err) {
      showToast('Failed to add placeholder', 'error');
    }
  };

  const handleEditPlaceholderInDb = (p, e) => {
    if (e && e.stopPropagation) e.stopPropagation();
    setEditModalConfig({
      title: 'Rename Placeholder Tag',
      label: 'Placeholder Name:',
      initialValue: p.name,
      onSave: async (newName) => {
        if (!newName || !newName.trim() || newName.trim() === p.name) return;
        await callEel('update_placeholder', p.id, newName.trim());
        showToast(`Renamed placeholder to "${newName.trim()}"!`, 'success');
        await loadPlaceholders();
      }
    });
  };

  const handleDeletePlaceholderFromDb = async (id, e) => {
    if (e && e.stopPropagation) e.stopPropagation();
    try {
      await callEel('delete_placeholder', id);
      showToast('Variable tag removed', 'success');
      await loadPlaceholders();
    } catch (err) {
      showToast('Failed to remove placeholder', 'error');
    }
  };


  // --- CATEGORIES, SETTING COLUMNS & SUBCATEGORIES CRUD ---
  const handleAddCategoryToDb = async (e) => {
    e.preventDefault();
    if (!newCatName.trim()) return;
    try {
      await callEel('add_category', newCatName.trim());
      showToast(`Category "${newCatName.trim()}" added to DB!`, 'success');
      setNewCatName('');
      setShowAddCatModal(false);
      await loadCategoriesAndColumns();
    } catch (err) {
      showToast('Failed to add category', 'error');
    }
  };

  const handleEditCategoryInDb = (cat) => {
    setEditModalConfig({
      title: 'Rename Category',
      label: 'Category Name:',
      initialValue: cat.name,
      onSave: async (newName) => {
        if (!newName || !newName.trim() || newName.trim() === cat.name) return;
        try {
          await callEel('update_category', cat.id, newName.trim());
          showToast(`Category renamed to "${newName.trim()}"!`, 'success');
          if (selectedHtmlCategory && selectedHtmlCategory.toLowerCase() === cat.name.toLowerCase()) {
            setSelectedHtmlCategory(newName.trim());
          }
          if (templateCatFilter && templateCatFilter.toLowerCase() === cat.name.toLowerCase()) {
            setTemplateCatFilter(newName.trim());
          }
          await loadCategoriesAndColumns();
          await loadCompanyHtmlTemplates();
        } catch (err) {
          showToast('Failed to rename category', 'error');
        }
      }
    });
  };

  const handleDeleteCategoryFromDb = async (id) => {
    if (!isAdminMode) {
      showToast('Admin Mode required to delete items! Double-click logo to unlock.', 'warning');
      return;
    }
    try {
      await callEel('delete_category', id);
      showToast('Category deleted from DB', 'success');
      await loadCategoriesAndColumns();
      await loadDatabaseItems();
      await reloadCompaniesAndProducts();
      setTemplateCatFilter('all');
    } catch (err) {
      showToast('Failed to delete category', 'error');
    }
  };

  const handleAddSubcategoryToDb = async (e, catForSubcat) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!newSubcatName.trim()) return;
    const targetCat = catForSubcat || newSubcatCat || selectedHtmlCategory || (dbCategories[0] ? dbCategories[0].name : 'Engagement Ring');
    try {
      await callEel('add_subcategory', targetCat, newSubcatName.trim());
      showToast(`Subcategory "${newSubcatName.trim()}" added to ${targetCat}!`, 'success');
      setNewSubcatName('');
      setNewSubcatCat('');
      setShowAddSubcatModal(false);
      await loadSubcategories(selectedHtmlCategory);
    } catch (err) {
      showToast('Failed to add subcategory', 'error');
    }
  };

  const handleEditSubcategoryInDb = (sub) => {
    setEditModalConfig({
      title: 'Rename Subcategory',
      label: 'Subcategory Name:',
      initialValue: sub.name,
      onSave: async (newName) => {
        if (!newName || !newName.trim() || newName.trim() === sub.name) return;
        try {
          await callEel('update_subcategory', sub.id, newName.trim(), sub.category);
          showToast(`Subcategory renamed to "${newName.trim()}"!`, 'success');
          if (selectedHtmlSubcategory && selectedHtmlSubcategory.toLowerCase() === sub.name.toLowerCase()) {
            setSelectedHtmlSubcategory(newName.trim());
          }
          await loadSubcategories(selectedHtmlCategory);
          await loadCompanyHtmlTemplates();
        } catch (err) {
          showToast('Failed to rename subcategory', 'error');
        }
      }
    });
  };

  const handleDeleteSubcategoryFromDb = async (id) => {
    if (!isAdminMode) {
      showToast('Admin Mode required to delete items! Double-click logo to unlock.', 'warning');
      return;
    }
    try {
      await callEel('delete_subcategory', id);
      showToast('Subcategory deleted from DB', 'success');
      await loadSubcategories();
      await loadCompanyHtmlTemplates();
      setSelectedHtmlSubcategory('Default');
    } catch (err) {
      showToast('Failed to delete subcategory', 'error');
    }
  };

  const handleAddSettingColumnToDb = async (e, catForCol) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!newColName.trim()) return;
    const targetCat = catForCol || newColCat || (templateCatFilter !== 'all' ? templateCatFilter : selectedHtmlCategory);
    try {
      await callEel('add_setting_column', newColName.trim(), targetCat !== 'all' ? targetCat : null);
      showToast(`Setting Column "${newColName.trim()}" added to ${targetCat && targetCat !== 'all' ? targetCat : 'DB'}!`, 'success');
      setNewColName('');
      setNewColCat('');
      setShowAddColModal(false);
      await loadCategoriesAndColumns();
    } catch (err) {
      showToast('Failed to add setting column', 'error');
    }
  };

  const handleEditSettingColumnInDb = (col) => {
    setEditModalConfig({
      title: 'Rename Setting Column',
      label: 'Setting Column Name:',
      initialValue: col.name,
      onSave: async (newName) => {
        if (!newName || !newName.trim() || newName.trim() === col.name) return;
        await callEel('update_setting_column', col.id, newName.trim());
        showToast(`Setting Column renamed to "${newName.trim()}"!`, 'success');
        await loadCategoriesAndColumns();
        await loadDatabaseItems();
      }
    });
  };

  const handleDeleteSettingColumnFromDb = async (id) => {
    if (!isAdminMode) {
      showToast('Admin Mode required to delete items! Double-click logo to unlock.', 'warning');
      return;
    }
    try {
      await callEel('delete_setting_column', id);
      showToast('Setting Column deleted from DB', 'success');
      await loadCategoriesAndColumns();
      await loadDatabaseItems();
      setTemplateSettingFilter('all');
    } catch (err) {
      showToast('Failed to delete setting column', 'error');
    }
  };

  // --- DATABASE CRUD HANDLERS ---
  const handleSavePolicy = async (e) => {
    e.preventDefault();
    if (!editingPolicy.company_name) {
      showToast('Company Name is required', 'warning');
      return;
    }
    try {
      await callEel('save_company_policy', editingPolicy);
      showToast('Company Policy saved to database!', 'success');
      setEditingPolicy(null);
      await loadDatabaseItems();
      await reloadCompaniesAndProducts();
    } catch (err) {
      showToast('Failed to save company policy', 'error');
    }
  };

  const handleDeletePolicy = async (id) => {
    if (!isAdminMode) {
      showToast('Admin Mode required to delete items! Double-click logo to unlock.', 'warning');
      return;
    }
    try {
      await callEel('delete_company_policy', id);
      showToast('Policy deleted from database', 'success');
      await loadDatabaseItems();
      await reloadCompaniesAndProducts();
    } catch (err) {
      showToast('Failed to delete policy', 'error');
    }
  };

  const handleSaveTemplate = async (e) => {
    e.preventDefault();
    if (!editingTemplate.template_text) {
      showToast('Template text is required', 'warning');
      return;
    }
    try {
      await callEel('save_title_template', editingTemplate);
      showToast('Title template saved to database!', 'success');
      setEditingTemplate(null);
      await loadDatabaseItems();
    } catch (err) {
      showToast('Failed to save title template', 'error');
    }
  };

  const handleDeleteTemplate = async (id) => {
    if (!isAdminMode) {
      showToast('Admin Mode required to delete items! Double-click logo to unlock.', 'warning');
      return;
    }
    try {
      await callEel('delete_title_template', id);
      showToast('Title template deleted', 'success');
      await loadDatabaseItems();
    } catch (err) {
      showToast('Failed to delete template', 'error');
    }
  };

  // Filtered title templates
  const filteredTemplates = templates.filter(t => {
    if (templateMetalFilter !== 'all' && t.metal_type.toLowerCase() !== templateMetalFilter.toLowerCase()) return false;
    if (templateCatFilter !== 'all' && t.product_category.toLowerCase() !== templateCatFilter.toLowerCase()) return false;
    if (templateSettingFilter !== 'all' && t.setting_column.toLowerCase() !== templateSettingFilter.toLowerCase()) return false;
    if (templateCompanyFilter !== 'all') {
      const compLower = templateCompanyFilter.toLowerCase();
      const tCompLower = (t.company_name || 'all').toLowerCase();
      if (tCompLower !== 'all' && tCompLower !== compLower) return false;
    }
    return true;
  });

  return (
    <div className="flex flex-1 p-4 gap-4 overflow-hidden h-screen text-gray-100 selection:bg-indigo-500 selection:text-white">
      {/* Navigation Sidebar */}
      {isSidebarVisible && (
        <nav
          style={{ width: `${sidebarWidth}px` }}
          className="glass-card p-4 flex flex-col justify-between relative shrink-0 select-none group/sidebar animate-fade-in"
        >
          {/* Vertical Resize Drag Handle */}
          <div
            onMouseDown={handleMouseDownResizer}
            className={`absolute top-0 right-0 w-2.5 h-full cursor-col-resize hover:bg-indigo-500/50 flex items-center justify-center transition-colors z-30 ${
              isResizingSidebar ? 'bg-indigo-500 shadow-lg shadow-indigo-500/50' : 'bg-transparent'
            }`}
            title="Click & drag to resize sidebar width"
          >
            <div className="w-0.5 h-10 bg-gray-500/40 group-hover/sidebar:bg-indigo-300 rounded"></div>
          </div>

          <div className="space-y-3 overflow-y-auto pr-1">
            {/* App Branding & Quick Status Header inside Left Sidebar */}
            <div className="p-3 glass-card bg-indigo-950/40 border-indigo-500/30 rounded-xl space-y-2.5 shadow-md">
              <div className="flex items-center justify-between">
                <div
                  onDoubleClick={handleLogoDoubleClick}
                  className="flex items-center space-x-2.5 cursor-pointer select-none group flex-1 min-w-0"
                  title={isAdminMode ? "Double-click logo to DEACTIVATE Admin Mode" : "Double-click logo & enter password 0000 to UNLOCK Delete options"}
                >
                  <div className={`w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg transition-all shrink-0 ${
                    isAdminMode ? 'ring-2 ring-rose-500 shadow-rose-500/50 scale-105' : 'shadow-indigo-500/30'
                  }`}>
                    <i className={`fa-solid ${isAdminMode ? 'fa-lock-open text-rose-300 animate-pulse' : 'fa-gem text-white'} text-sm`}></i>
                  </div>
                  <div className="min-w-0 flex-1">
                    <h1 className="text-xs font-bold text-white tracking-wide truncate">
                      Jewelry Data Engine
                    </h1>
                    <p className="text-[10px] text-gray-400 truncate">
                      {isAdminMode ? 'Admin Unlocked' : 'Double-click logo for Admin'}
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={toggleSidebar}
                  className="w-7 h-7 rounded-lg bg-white/5 hover:bg-rose-500/20 text-gray-400 hover:text-rose-300 flex items-center justify-center transition-all border border-white/10 shrink-0 ml-1"
                  title="Hide / Collapse Left Navigation Sidebar"
                >
                  <i className="fa-solid fa-angles-left text-xs"></i>
                </button>
              </div>

            {isAdminMode && (
              <div className="flex items-center justify-between pt-1 border-t border-white/10">
                <span className="px-2 py-0.5 text-[9px] font-bold rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 uppercase tracking-wider animate-pulse flex items-center space-x-1">
                  <i className="fa-solid fa-shield-halved text-[8px]"></i>
                  <span>Admin ON</span>
                </span>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setChangePassCurrent('');
                    setChangePassNew('');
                    setChangePassConfirm('');
                    setShowChangePassModal(true);
                  }}
                  className="px-2 py-0.5 text-[9px] font-bold rounded-full bg-indigo-500/20 hover:bg-indigo-500/40 text-indigo-300 border border-indigo-500/40 transition-all flex items-center space-x-1"
                  title="Change Admin Password"
                >
                  <i className="fa-solid fa-key text-[8px]"></i>
                  <span>Change Pass</span>
                </button>
              </div>
            )}

            {/* DB Status & Clear Multi_API Action */}
            <div className="pt-2 border-t border-white/10 flex flex-col space-y-1.5">
              <div className="flex items-center justify-between text-[11px] text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                <span className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] inline-block"></span>
                  <span className="font-semibold text-[10px]">DB Connected</span>
                </span>
                <i className="fa-solid fa-database text-[10px]"></i>
              </div>

              <button 
                onClick={handleClearExcel}
                disabled={isClearing}
                className={`w-full py-1.5 text-[11px] font-semibold rounded-lg flex items-center justify-center space-x-1.5 transition-all ${
                  clearStatus 
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    : 'bg-white/5 hover:bg-white/10 text-amber-300 border border-white/10'
                }`}
              >
                <i className={`fa-solid ${clearStatus ? 'fa-check text-emerald-400' : 'fa-broom text-amber-400'}`}></i>
                <span>{clearStatus ? 'Multi_API.xlsx Cleared' : 'Clear Multi_API.xlsx'}</span>
              </button>

              <div className="grid grid-cols-2 gap-1.5 pt-1">
                <a
                  href="/main-app/download-output/?type=latest"
                  download
                  className="py-1 px-2 text-[10px] font-semibold rounded bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 text-center flex items-center justify-center space-x-1 transition-all"
                  title="Download Latest Generated API File (API-*.xlsx)"
                >
                  <i className="fa-solid fa-file-arrow-down text-[10px]"></i>
                  <span>Latest API</span>
                </a>
                <a
                  href="/main-app/download-output/?type=multi"
                  download="Multi_API.xlsx"
                  className="py-1 px-2 text-[10px] font-semibold rounded bg-indigo-500/15 hover:bg-indigo-500/25 text-indigo-300 border border-indigo-500/30 text-center flex items-center justify-center space-x-1 transition-all"
                  title="Download Multi_API.xlsx"
                >
                  <i className="fa-solid fa-file-excel text-[10px]"></i>
                  <span>Multi_API</span>
                </a>
              </div>
            </div>
          </div>

          <div className="px-2 text-[11px] font-bold text-gray-400 uppercase tracking-wider flex items-center justify-between">
            <span>Navigation</span>
            <button
              onClick={() => {
                setTempNavLabels(navLabels);
                setShowCustomizeNavModal(true);
              }}
              className="text-gray-400 hover:text-indigo-300 p-0.5 rounded transition-colors"
              title="Customize Navigation Bar Tab Titles"
            >
              <i className="fa-solid fa-gear text-xs"></i>
            </button>
          </div>

            <div className="space-y-1">
              <button
                onClick={() => handleNavTabClick('generator')}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-xs transition-all ${
                  activeTab === 'generator'
                    ? 'bg-gradient-to-r from-indigo-600/80 to-purple-600/80 text-white shadow-lg shadow-indigo-500/25 border border-indigo-400/30 font-bold'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <span className="flex items-center space-x-3 truncate">
                  <i className="fa-solid fa-wand-magic-sparkles text-sm"></i>
                  <span className="truncate">{navLabels.generator || 'Data Generator Master'}</span>
                </span>
                {activeTab === 'generator' && (
                  <i className={`fa-solid ${collapsedNavPanels['generator'] ? 'fa-chevron-down' : 'fa-chevron-up'} text-[10px] text-indigo-200 ml-1 transition-transform`}></i>
                )}
              </button>

              <button
                onClick={() => handleNavTabClick('html_master')}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-xs transition-all ${
                  activeTab === 'html_master'
                    ? 'bg-gradient-to-r from-purple-600/80 to-indigo-600/80 text-white shadow-lg shadow-purple-500/25 border border-purple-400/30 font-bold'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <span className="flex items-center space-x-3 truncate">
                  <i className="fa-solid fa-code text-sm text-purple-400"></i>
                  <span className="truncate">{navLabels.html_master || 'HTML App (Modifier) Master'}</span>
                </span>
                {activeTab === 'html_master' && (
                  <i className={`fa-solid ${collapsedNavPanels['html_master'] ? 'fa-chevron-down' : 'fa-chevron-up'} text-[10px] text-purple-200 ml-1 transition-transform`}></i>
                )}
              </button>
            </div>

            {/* Left Sidebar HTML Target Controls & Action Panel */}
            {(activeTab === 'html_master' || (activeTab === 'database' && dbSubTab === 'html_templates')) && !collapsedNavPanels['html_master'] && (
              <div className="p-3.5 bg-black/60 border border-purple-500/30 rounded-xl space-y-3 animate-fade-in shadow-inner">
                <div className="text-[11px] font-bold text-purple-300 uppercase tracking-wider flex items-center justify-between pb-2 border-b border-white/10">
                  <span className="flex items-center space-x-1.5">
                    <i className="fa-solid fa-sliders text-indigo-400"></i>
                    <span>HTML Controls</span>
                  </span>
                  <span className="text-[10px] text-gray-400 font-mono">Sidebar</span>
                </div>

                {/* Company Select */}
                <div>
                  <label className="block text-[11px] font-bold text-gray-300 mb-1">Company Scope:</label>
                  <select
                    value={selectedHtmlCompany}
                    onChange={(e) => setSelectedHtmlCompany(e.target.value)}
                    className="w-full glass-input px-2.5 py-1.5 text-xs font-semibold text-indigo-300 truncate"
                  >
                    {companies.map((c, idx) => (
                      <option key={idx} value={c} className="bg-gray-900 text-white">{c}</option>
                    ))}
                  </select>
                </div>

                {/* Category Select + Add / Delete */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="block text-[11px] font-bold text-gray-300">Category:</label>
                    <button
                      onClick={() => setShowAddCatModal(true)}
                      className="text-[10px] text-purple-300 hover:text-white font-bold underline"
                    >
                      + New
                    </button>
                  </div>
                  <div className="flex items-center space-x-1">
                    <select
                      value={selectedHtmlCategory}
                      onChange={(e) => setSelectedHtmlCategory(e.target.value)}
                      className="w-full glass-input px-2.5 py-1.5 text-xs font-semibold text-purple-300 truncate"
                    >
                      {dbCategories.map((c, idx) => (
                        <option key={idx} value={c.name} className="bg-gray-900">{c.name}</option>
                      ))}
                    </select>
                    {isAdminMode && selectedHtmlCategory && selectedHtmlCategory.toLowerCase() !== 'default' && (
                      <div className="flex items-center space-x-1 shrink-0">
                        <button
                          onClick={() => {
                            const catObj = dbCategories.find(c => c.name.toLowerCase() === selectedHtmlCategory.toLowerCase());
                            if (catObj) handleEditCategoryInDb(catObj);
                          }}
                          className="px-2 py-1.5 text-xs rounded bg-indigo-500/20 hover:bg-indigo-500/40 text-indigo-300 border border-indigo-500/30 transition-colors"
                          title={`Rename category "${selectedHtmlCategory}"`}
                        >
                          <i className="fa-solid fa-pen text-[10px]"></i>
                        </button>
                        <button
                          onClick={() => {
                            const catObj = dbCategories.find(c => c.name.toLowerCase() === selectedHtmlCategory.toLowerCase());
                            if (catObj) handleDeleteCategoryFromDb(catObj.id);
                          }}
                          className="px-2 py-1.5 text-xs rounded bg-rose-500/20 hover:bg-rose-500/40 text-rose-300 border border-rose-500/30 transition-colors"
                          title={`Delete category "${selectedHtmlCategory}"`}
                        >
                          <i className="fa-solid fa-trash text-[10px]"></i>
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Subcategory Select + Add / Delete */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="block text-[11px] font-bold text-gray-300">Subcategory:</label>
                    <button
                      onClick={() => setShowAddSubcatModal(true)}
                      className="text-[10px] text-emerald-300 hover:text-white font-bold underline"
                    >
                      + New
                    </button>
                  </div>
                  <div className="flex items-center space-x-1">
                    <select
                      value={selectedHtmlSubcategory}
                      onChange={(e) => setSelectedHtmlSubcategory(e.target.value)}
                      className="w-full glass-input px-2.5 py-1.5 text-xs font-semibold text-emerald-300 truncate"
                    >
                      {sortWithDefaultFirst(dbSubcategories.filter(s => !s.category || s.category.toLowerCase() === (selectedHtmlCategory || '').toLowerCase())).map((sub, idx) => (
                        <option key={idx} value={sub.name} className="bg-gray-900">{sub.name}</option>
                      ))}
                    </select>
                    {isAdminMode && selectedHtmlSubcategory && selectedHtmlSubcategory.toLowerCase() !== 'default' && (
                      <div className="flex items-center space-x-1 shrink-0">
                        <button
                          onClick={() => {
                            const subObj = dbSubcategories.find(s => s.name.toLowerCase() === selectedHtmlSubcategory.toLowerCase() && (!s.category || s.category.toLowerCase() === (selectedHtmlCategory || '').toLowerCase()));
                            if (subObj) handleEditSubcategoryInDb(subObj);
                          }}
                          className="px-2 py-1.5 text-xs rounded bg-indigo-500/20 hover:bg-indigo-500/40 text-indigo-300 border border-indigo-500/30 transition-colors"
                          title={`Rename subcategory "${selectedHtmlSubcategory}"`}
                        >
                          <i className="fa-solid fa-pen text-[10px]"></i>
                        </button>
                        <button
                          onClick={() => {
                            const subObj = dbSubcategories.find(s => s.name.toLowerCase() === selectedHtmlSubcategory.toLowerCase() && (!s.category || s.category.toLowerCase() === (selectedHtmlCategory || '').toLowerCase()));
                            if (subObj) handleDeleteSubcategoryFromDb(subObj.id);
                          }}
                          className="px-2 py-1.5 text-xs rounded bg-rose-500/20 hover:bg-rose-500/40 text-rose-300 border border-rose-500/30 transition-colors"
                          title={`Delete subcategory "${selectedHtmlSubcategory}"`}
                        >
                          <i className="fa-solid fa-trash text-[10px]"></i>
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Action Buttons Stack */}
                <div className="pt-2 space-y-2 border-t border-white/10">
                  <button
                    onClick={handleSaveCompanyHtmlTemplate}
                    disabled={isSavingHtml}
                    className="btn-primary w-full py-2 text-xs font-bold flex items-center justify-center space-x-2 shadow-lg shadow-indigo-500/20"
                  >
                    <i className={`fa-solid ${isSavingHtml ? 'fa-circle-notch fa-spin' : 'fa-floppy-disk'}`}></i>
                    <span>Save HTML to DB</span>
                  </button>

                  <div className="grid grid-cols-2 gap-1.5">
                    <button
                      onClick={() => setIsVisualEditing(!isVisualEditing)}
                      className={`px-2 py-1.5 text-[11px] font-semibold rounded-lg flex items-center justify-center space-x-1 border transition-all ${
                        isVisualEditing
                          ? 'bg-purple-600/40 text-purple-200 border-purple-400 shadow-md shadow-purple-500/20 animate-pulse'
                          : 'bg-white/5 text-gray-400 border-white/10 hover:text-white'
                      }`}
                      title="Edit elements directly inside Live Preview window"
                    >
                      <i className="fa-solid fa-pen-to-square text-[10px]"></i>
                      <span>{isVisualEditing ? 'Visual ON' : 'Visual OFF'}</span>
                    </button>

                    <button
                      onClick={() => setShowLivePreview(!showLivePreview)}
                      className={`px-2 py-1.5 text-[11px] font-semibold rounded-lg flex items-center justify-center space-x-1 border transition-all ${
                        showLivePreview
                          ? 'bg-indigo-600/30 text-indigo-200 border-indigo-500/50'
                          : 'bg-white/5 text-gray-400 border-white/10 hover:text-white'
                      }`}
                      title="Toggle Side-by-Side Live Preview"
                    >
                      <i className="fa-solid fa-columns text-[10px]"></i>
                      <span>{showLivePreview ? 'Hide Split' : 'Show Split'}</span>
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-1.5">
                    <button
                      onClick={handleResetCompanyHtmlTemplate}
                      className="px-2 py-1.5 text-[11px] font-semibold rounded-lg bg-amber-500/10 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30 flex items-center justify-center space-x-1 transition-all"
                      title="Reset/Undo unsaved changes to fresh database version"
                    >
                      <i className="fa-solid fa-rotate-left text-[10px]"></i>
                      <span>Reset</span>
                    </button>

                    {isAdminMode && (
                      <button
                        onClick={handleDeleteCompanyHtmlTemplate}
                        className="px-2 py-1.5 text-[11px] font-semibold rounded-lg bg-rose-500/10 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 flex items-center justify-center space-x-1 transition-all"
                        title="Delete custom HTML template entry from DB"
                      >
                        <i className="fa-solid fa-trash text-[10px]"></i>
                        <span>Delete</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-1 pt-1 border-t border-white/10">
              <button
                onClick={() => handleNavTabClick('database')}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-xs transition-all ${
                  activeTab === 'database'
                    ? 'bg-gradient-to-r from-indigo-600/80 to-purple-600/80 text-white shadow-lg shadow-indigo-500/25 border border-indigo-400/30 font-bold'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <span className="flex items-center space-x-3 truncate">
                  <i className="fa-solid fa-database text-sm"></i>
                  <span className="truncate">{navLabels.database || 'Database Manager Master'}</span>
                </span>
                {activeTab === 'database' && (
                  <i className={`fa-solid ${collapsedNavPanels['database'] ? 'fa-chevron-down' : 'fa-chevron-up'} text-[10px] text-indigo-200 ml-1 transition-transform`}></i>
                )}
              </button>

              {/* Nested Database Sub-tabs when activeTab === 'database' */}
              {activeTab === 'database' && !collapsedNavPanels['database'] && (
                <div className="pl-3 py-1.5 space-y-1 border-l-2 border-indigo-500/40 ml-4 animate-fade-in">
                  <button
                    onClick={() => setDbSubTab('policies')}
                    className={`w-full flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      dbSubTab === 'policies'
                        ? 'bg-indigo-600/40 text-indigo-200 border border-indigo-500/40 shadow-sm'
                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <i className="fa-solid fa-building text-[11px]"></i>
                    <span>Policies</span>
                  </button>

                  <button
                    onClick={() => setDbSubTab('templates')}
                    className={`w-full flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      dbSubTab === 'templates'
                        ? 'bg-indigo-600/40 text-indigo-200 border border-indigo-500/40 shadow-sm'
                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <i className="fa-solid fa-font text-[11px]"></i>
                    <span>Title Formulas</span>
                  </button>

                  <button
                    onClick={() => setDbSubTab('categories')}
                    className={`w-full flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      dbSubTab === 'categories'
                        ? 'bg-indigo-600/40 text-indigo-200 border border-indigo-500/40 shadow-sm'
                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <i className="fa-solid fa-list text-[11px]"></i>
                    <span>Categories & Columns</span>
                  </button>

                  <button
                    onClick={() => {
                      setDbSubTab('backup');
                      fetchBackupsList();
                    }}
                    className={`w-full flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      dbSubTab === 'backup'
                        ? 'bg-indigo-600/40 text-indigo-200 border border-indigo-500/40 shadow-sm'
                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <i className="fa-solid fa-database text-[11px]"></i>
                    <span>DB Backup & Restore</span>
                  </button>
                </div>
              )}
            </div>

            <div className="space-y-1">
              <button
                onClick={() => handleNavTabClick('mapping')}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all ${
                  activeTab === 'mapping'
                    ? 'bg-gradient-to-r from-indigo-600/80 to-purple-600/80 text-white shadow-lg shadow-indigo-500/25 border border-indigo-400/30 font-bold'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <span className="flex items-center space-x-3 truncate">
                  <i className="fa-solid fa-table-columns text-sm"></i>
                  <span className="truncate">{navLabels.mapping || 'Excel Mapping Master'}</span>
                </span>
                {activeTab === 'mapping' && (
                  <i className={`fa-solid ${collapsedNavPanels['mapping'] ? 'fa-chevron-down' : 'fa-chevron-up'} text-[10px] text-indigo-200 ml-1 transition-transform`}></i>
                )}
              </button>

              {/* Left Sidebar Excel Mapping Controls Panel */}
              {activeTab === 'mapping' && !collapsedNavPanels['mapping'] && (
                <div className="p-3.5 bg-black/60 border border-indigo-500/30 rounded-xl space-y-3 animate-fade-in shadow-inner">
                  <div className="text-[11px] font-bold text-indigo-300 uppercase tracking-wider flex items-center justify-between pb-2 border-b border-white/10">
                    <span className="flex items-center space-x-1.5">
                      <i className="fa-solid fa-filter text-indigo-400"></i>
                      <span>Mapping Controls</span>
                    </span>
                    <span className="text-[10px] text-gray-400 font-mono">Sidebar</span>
                  </div>

                  {/* Search Input */}
                  <div>
                    <label className="block text-[11px] font-bold text-gray-300 mb-1">Search Rule:</label>
                    <div className="relative">
                      <i className="fa-solid fa-magnifying-glass absolute left-2.5 top-2.5 text-[10px] text-gray-400"></i>
                      <input
                        type="text"
                        placeholder="Search column, sheet..."
                        value={mappingSearch}
                        onChange={(e) => setMappingSearch(e.target.value)}
                        className="w-full glass-input pl-7 pr-2.5 py-1.5 text-xs text-white placeholder-gray-500"
                      />
                    </div>
                  </div>

                  {/* Company Filter */}
                  <div>
                    <label className="block text-[11px] font-bold text-gray-300 mb-1">Company Scope:</label>
                    <select
                      value={mappingFilterCompany}
                      onChange={(e) => setMappingFilterCompany(e.target.value)}
                      className="w-full glass-input px-2.5 py-1.5 text-xs font-semibold text-amber-300 truncate"
                    >
                      <option value="all">All Companies ({companies.length})</option>
                      <option value="All">✨ Global Rules Only (All)</option>
                      {companies.map(c => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>

                  {/* Source Sheet Filter */}
                  <div>
                    <label className="block text-[11px] font-bold text-gray-300 mb-1">Input Sheet:</label>
                    <select
                      value={mappingFilterSource}
                      onChange={(e) => setMappingFilterSource(e.target.value)}
                      className="w-full glass-input px-2.5 py-1.5 text-xs font-semibold text-indigo-300 truncate"
                    >
                      <option value="all">All File Sheets ({availableInputSheets.length})</option>
                      <option value="[ALL]">✨ [ALL] (Global Rules Only)</option>
                      {availableInputSheets.map(s => (
                        <option key={s} value={s}>Input: {s}</option>
                      ))}
                    </select>
                  </div>

                  {/* Target Sheet Filter */}
                  <div>
                    <label className="block text-[11px] font-bold text-gray-300 mb-1">Target Sheet:</label>
                    <select
                      value={mappingFilterTarget}
                      onChange={(e) => setMappingFilterTarget(e.target.value)}
                      className="w-full glass-input px-2.5 py-1.5 text-xs font-semibold text-purple-300 truncate"
                    >
                      <option value="all">All Target Sheets ({availableTargetSheets.length})</option>
                      <option value="[ALL]">✨ [ALL] (Global Rules Only)</option>
                      {getFilteredTargetSheets(mappingFilterSource, availableTargetSheets).map(t => (
                        <option key={t} value={t}>Target: {t}</option>
                      ))}
                    </select>
                  </div>

                  {/* Target Column Filter */}
                  <div>
                    <label className="block text-[11px] font-bold text-gray-300 mb-1">Target Column:</label>
                    <select
                      value={mappingFilterColumn}
                      onChange={(e) => setMappingFilterColumn(e.target.value)}
                      className="w-full glass-input px-2.5 py-1.5 text-xs font-semibold text-emerald-300 truncate"
                    >
                      <option value="all">All Columns ({availableTargetColumns.length})</option>
                      {availableTargetColumns.map(c => (
                        <option key={c} value={c}>Column: {c}</option>
                      ))}
                    </select>
                  </div>

                  {/* Sort Order */}
                  <div>
                    <label className="block text-[11px] font-bold text-gray-300 mb-1">Sort Order:</label>
                    <select
                      value={mappingSortBy}
                      onChange={(e) => setMappingSortBy(e.target.value)}
                      className="w-full glass-input px-2.5 py-1.5 text-xs font-semibold text-blue-300 truncate"
                    >
                      <option value="id_asc">🕒 Order Added (ID)</option>
                      <option value="alpha_target_col">🔤 Column Name (A → Z)</option>
                      <option value="alpha_target_sheet">📁 Target Sheet (A → Z)</option>
                      <option value="alpha_source_sheet">📄 Source Sheet (A → Z)</option>
                      <option value="alpha_company">🏢 Company Name (A → Z)</option>
                    </select>
                  </div>

                  {/* Action Buttons */}
                  <div className="pt-2 space-y-2 border-t border-white/10">
                    <button
                      onClick={() => {
                        setEditingMapping({ source_sheet: availableInputSheets[0] || 'RING', source_column: '', target_sheet: availableTargetSheets[0] || 'Cat-EngagementRings', target_column: '', mapping_type: 'direct', default_value: '' });
                        setShowMappingModal(true);
                      }}
                      className="btn-primary w-full py-2 text-xs font-bold flex items-center justify-center space-x-2 shadow-lg shadow-indigo-500/20"
                    >
                      <i className="fa-solid fa-plus text-xs"></i>
                      <span>Add Column Mapping</span>
                    </button>

                    <div className="grid grid-cols-2 gap-1.5">
                      <button
                        onClick={handleRefreshSheets}
                        className="px-2 py-1.5 text-[11px] font-semibold rounded-lg bg-emerald-600/30 hover:bg-emerald-600/50 text-emerald-200 border border-emerald-500/40 flex items-center justify-center space-x-1 transition-all"
                        title="Rescan data.xlsx and keep only sheets present in file"
                      >
                        <i className="fa-solid fa-arrows-rotate text-[10px]"></i>
                        <span>Refresh</span>
                      </button>

                      <button
                        onClick={handleResetMappings}
                        className="px-2 py-1.5 text-[11px] font-semibold rounded-lg bg-gray-800/80 hover:bg-gray-700 text-gray-300 border border-gray-700 flex items-center justify-center space-x-1 transition-all"
                        title="Restore default standard category mappings"
                      >
                        <i className="fa-solid fa-rotate-left text-[10px]"></i>
                        <span>Reset</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

              <button
                onClick={() => setActiveTab('settings')}
                className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all ${
                  activeTab === 'settings'
                    ? 'bg-gradient-to-r from-indigo-600/80 to-purple-600/80 text-white shadow-lg shadow-indigo-500/25 border border-indigo-400/30 font-bold'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <i className="fa-solid fa-circle-info text-sm"></i>
                <span className="truncate">{navLabels.settings || 'System Info Master'}</span>
              </button>
            </div>

          {/* Sidebar Footer info */}
          <div className="p-3 glass-card bg-indigo-950/30 border-indigo-500/20 text-xs text-gray-400 rounded-xl space-y-1">
            <div className="flex justify-between items-center text-gray-300 font-medium">
              <span>Active Company</span>
              <span className="text-indigo-400 truncate max-w-[100px]">{selectedCompany || 'None'}</span>
            </div>
            <div className="flex justify-between items-center text-gray-300 font-medium">
              <span>Active Product</span>
              <span className="text-purple-400 truncate max-w-[100px]">{selectedProduct || 'None'}</span>
            </div>
          </div>
        </nav>
      )}

        {/* Main Content Area */}
        <main className={`flex-1 glass-card p-6 flex flex-col min-h-0 overflow-y-auto relative transition-all ${!isSidebarVisible ? 'pl-14' : ''}`}>
          {!isSidebarVisible && (
            <button
              type="button"
              onClick={toggleSidebar}
              className="absolute top-5 left-3.5 z-40 w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-xl border border-indigo-400/50 flex items-center justify-center transition-all hover:scale-110 active:scale-95 cursor-pointer"
              title="Show / Expand Left Navigation Sidebar (Press Esc key to toggle)"
            >
              <i className="fa-solid fa-angles-right text-xs"></i>
            </button>
          )}
          {activeTab === 'generator' && (
            <div className="max-w-3xl mx-auto space-y-8">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-white/10">
                <div>
                  <h2 className="text-2xl font-bold text-white flex items-center space-x-3">
                    <i className="fa-solid fa-bolt text-indigo-400"></i>
                    <span>Data Generator & API Exporter</span>
                  </h2>
                  <p className="text-gray-400 text-sm mt-1">
                    Select database-backed company business policy and product category to run title generator & API export.
                  </p>
                </div>

                {/* Schedule Time (PDT) Quick Helper (Replaces legacy Schedule time.py) */}
                <div className="glass-card bg-indigo-950/40 border-indigo-500/30 p-2.5 rounded-xl shadow-lg flex flex-col space-y-1.5 self-start sm:self-auto min-w-[270px]">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-300 flex items-center space-x-1.5">
                      <i className="fa-regular fa-clock text-indigo-400"></i>
                      <span>Schedule Time (PDT)</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowScheduleSettings(!showScheduleSettings)}
                      className="text-gray-400 hover:text-white text-xs px-1.5 py-0.5 rounded hover:bg-white/10 transition-colors"
                      title="Adjust Schedule Offset (Days/Hours/Mins)"
                    >
                      <i className="fa-solid fa-sliders text-[10px]"></i>
                    </button>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-semibold text-emerald-300 bg-black/40 px-2 py-1 rounded border border-emerald-500/20 select-all">
                      {scheduleTime || 'Loading...'}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleCopySchedule()}
                      className={`px-2.5 py-1 text-xs font-bold rounded flex items-center space-x-1 transition-all ${
                        scheduleCopied
                          ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/30'
                          : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-500/30'
                      }`}
                      title="Click to copy timestamp (e.g. for eBay schedule time)"
                    >
                      <i className={`fa-solid ${scheduleCopied ? 'fa-check' : 'fa-copy'} text-[10px]`}></i>
                      <span>{scheduleCopied ? 'Copied!' : 'Copy'}</span>
                    </button>
                  </div>

                  {showScheduleSettings && (
                    <div className="pt-2 mt-1 border-t border-white/10 space-y-2 animate-fade-in text-[11px]">
                      <div className="grid grid-cols-3 gap-1.5">
                        <div>
                          <label className="text-[10px] text-gray-400 block">Days</label>
                          <input
                            type="number"
                            min="0"
                            value={scheduleDays}
                            onChange={(e) => setScheduleDays(parseInt(e.target.value) || 0)}
                            className="w-full bg-black/40 border border-white/10 rounded px-1.5 py-0.5 text-center text-white font-mono"
                          />
                        </div>
                        <div>
                          <label className="text-[10px] text-gray-400 block">Hours</label>
                          <input
                            type="number"
                            min="0"
                            max="23"
                            value={scheduleHours}
                            onChange={(e) => setScheduleHours(parseInt(e.target.value) || 0)}
                            className="w-full bg-black/40 border border-white/10 rounded px-1.5 py-0.5 text-center text-white font-mono"
                          />
                        </div>
                        <div>
                          <label className="text-[10px] text-gray-400 block">Mins</label>
                          <input
                            type="number"
                            min="0"
                            max="59"
                            value={scheduleMinutes}
                            onChange={(e) => setScheduleMinutes(parseInt(e.target.value) || 0)}
                            className="w-full bg-black/40 border border-white/10 rounded px-1.5 py-0.5 text-center text-white font-mono"
                          />
                        </div>
                      </div>
                      <div className="flex items-center justify-between pt-1">
                        <button
                          type="button"
                          onClick={() => { setScheduleDays(0); setScheduleHours(7); setScheduleMinutes(15); }}
                          className="text-[10px] text-indigo-300 hover:text-white underline"
                        >
                          Reset to +7h 15m
                        </button>
                        <button
                          type="button"
                          onClick={() => { setScheduleDays(0); setScheduleHours(0); setScheduleMinutes(0); }}
                          className="text-[10px] text-gray-400 hover:text-white"
                        >
                          Now (PDT)
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Selection Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Company Card */}
                <div className="p-5 glass-card bg-white/[0.02] border-white/10 space-y-3">
                  <div className="flex justify-between items-center">
                    <label className="block text-sm font-semibold text-gray-200 flex items-center space-x-2">
                      <i className="fa-solid fa-building text-indigo-400"></i>
                      <span>Target Company</span>
                    </label>
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => setEditingPolicy({ company_name: '', shipping_profile_name: '', return_profile_name: '', payment_profile_name: '', brand_name: '', location: '' })}
                        className="px-2 py-0.5 text-xs rounded bg-indigo-500/20 hover:bg-indigo-500/40 text-indigo-300 border border-indigo-500/30 font-semibold"
                        title="Add New Company Policy"
                      >
                        + Add
                      </button>
                      {isAdminMode && selectedCompany && (
                        <button
                          onClick={() => {
                            const polObj = policies.find(p => p.company_name.toLowerCase() === selectedCompany.toLowerCase());
                            if (polObj) handleDeletePolicy(polObj.id);
                          }}
                          className="px-2 py-0.5 text-xs rounded bg-rose-500/20 hover:bg-rose-500/40 text-rose-300 border border-rose-500/30"
                          title={`Delete policy for ${selectedCompany}`}
                        >
                          <i className="fa-solid fa-trash text-[10px]"></i>
                        </button>
                      )}
                    </div>
                  </div>
                  <select
                    value={selectedCompany}
                    onChange={handleCompanyChange}
                    className="w-full glass-input px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="" className="bg-gray-900 text-gray-400">Select Company...</option>
                    {companies.map((comp, idx) => (
                      <option key={idx} value={comp} className="bg-gray-900 text-white">
                        {comp}
                      </option>
                    ))}
                  </select>

                  {selectedCompany && (
                    <div className="flex items-center justify-between p-2.5 rounded-lg bg-black/25 border border-white/5 text-xs animate-fade-in">
                      <div className="flex items-center space-x-2 min-w-0">
                        {companyBlueprintInfo && companyBlueprintInfo.exists ? (
                          <>
                            <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)] shrink-0"></span>
                            <span className="text-emerald-300 font-medium truncate" title={`Blueprint: ${companyBlueprintInfo.filename}`}>
                              Blueprint: <span className="text-white font-semibold">{companyBlueprintInfo.filename}</span> ({companyBlueprintInfo.size_kb} KB)
                            </span>
                          </>
                        ) : (
                          <>
                            <span className="w-2 h-2 rounded-full bg-amber-400 shrink-0"></span>
                            <span className="text-amber-300 font-medium truncate">No custom blueprint (Multi_API.xlsx fallback)</span>
                          </>
                        )}
                      </div>
                      <div className="flex items-center space-x-1.5 shrink-0 ml-2">
                        <label className="cursor-pointer px-2.5 py-1 rounded bg-indigo-600/40 hover:bg-indigo-600/60 text-indigo-200 border border-indigo-400/30 font-semibold flex items-center space-x-1 transition-all" title="Upload or replace master blueprint (.xlsx)">
                          <i className="fa-solid fa-cloud-arrow-up text-[10px]"></i>
                          <span>{companyBlueprintInfo && companyBlueprintInfo.exists ? 'Replace' : 'Upload'} Blueprint</span>
                          <input
                            type="file"
                            accept=".xlsx,.xls"
                            className="hidden"
                            onChange={(e) => {
                              const f = e.target.files && e.target.files[0];
                              if (f) handleUploadCompanyBlueprint(selectedCompany, f);
                              e.target.value = '';
                            }}
                          />
                        </label>
                        {companyBlueprintInfo && companyBlueprintInfo.exists && (
                          <a
                            href={`/main-app/download-output/?type=blueprint&company=${encodeURIComponent(selectedCompany)}`}
                            download={`${selectedCompany}.xlsx`}
                            className="p-1 px-2 rounded bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 transition-colors"
                            title="Download Current Master Blueprint Template"
                          >
                            <i className="fa-solid fa-download text-[11px]"></i>
                          </a>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Product Card - Auto-Detect All Sheets */}
                <div className="p-5 glass-card bg-purple-950/20 border-purple-500/30 space-y-3">
                  <div className="flex justify-between items-center flex-wrap gap-2">
                    <label className="block text-sm font-semibold text-purple-200 flex items-center space-x-2">
                      <i className="fa-solid fa-layer-group text-purple-400"></i>
                      <span>Detected Input File Sheets</span>
                    </label>
                    <div className="flex items-center space-x-2">
                      <label className="cursor-pointer px-2.5 py-1 text-xs rounded-lg bg-indigo-600/40 hover:bg-indigo-600/60 text-indigo-200 border border-indigo-400/30 font-semibold flex items-center space-x-1.5 transition-all shadow-sm" title="Upload and replace data.xlsx directly">
                        <i className="fa-solid fa-cloud-arrow-up text-[11px] text-indigo-300"></i>
                        <span>Upload data.xlsx</span>
                        <input
                          type="file"
                          accept=".xlsx,.xls"
                          className="hidden"
                          onChange={handleUploadDataXlsx}
                        />
                      </label>
                      <span className="px-2.5 py-1 text-xs rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold flex items-center space-x-1">
                        <i className="fa-solid fa-check text-[10px]"></i>
                        <span>Auto-Processing All</span>
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 pt-1">
                    {availableInputSheets.map((sheet, idx) => (
                      <span key={idx} className="px-3 py-1.5 rounded-lg bg-gray-900/90 border border-purple-500/40 text-xs font-semibold text-purple-200 flex items-center space-x-1.5 shadow-md">
                        <i className="fa-solid fa-file-excel text-emerald-400"></i>
                        <span>{sheet}</span>
                      </span>
                    ))}
                  </div>
                  <p className="text-[11px] text-gray-400 flex items-center gap-1.5">
                    <i className="fa-solid fa-database text-indigo-400"></i>
                    <span>Product records are loaded directly from <b>SQLite Database (100x Faster)</b>. Processed across all sheets in one pass.</span>
                  </p>
                </div>
              </div>


              {/* Variations Toggle Panel */}
              <div className="p-6 glass-card bg-indigo-950/20 border-indigo-500/20 space-y-6">
                <h3 className="text-sm font-bold uppercase tracking-wider text-indigo-300 flex items-center space-x-2">
                  <i className="fa-solid fa-sliders text-indigo-400"></i>
                  <span>Variation Generators</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Color Variation Toggle */}
                  <div className="flex items-center justify-between p-4 rounded-xl bg-white/[0.03] border border-white/5">
                    <div>
                      <div className="font-semibold text-sm text-gray-200">Color Variation</div>
                      <div className="text-xs text-gray-400">Generate Rose, Yellow & White Gold listings</div>
                    </div>
                    <label className="switch">
                      <input 
                        type="checkbox" 
                        checked={colorVariation} 
                        onChange={handleColorVariationToggle}
                      />
                      <span className="slider"></span>
                    </label>
                  </div>

                  {/* Gold Purity Variation Toggle */}
                  <div className="flex items-center justify-between p-4 rounded-xl bg-white/[0.03] border border-white/5">
                    <div>
                      <div className="font-semibold text-sm text-gray-200">Gold Purity Variation</div>
                      <div className="text-xs text-gray-400">Generate 10k, 14k, 18k variations</div>
                    </div>
                    <label className="switch">
                      <input 
                        type="checkbox" 
                        checked={goldPurityVariation} 
                        onChange={handleGoldPurityToggle}
                      />
                      <span className="slider"></span>
                    </label>
                  </div>
                </div>
              </div>

              {/* Big Process Button */}
              <div className="pt-4 flex flex-col items-center justify-center space-y-4">
                <button
                  onClick={handleProcessClick}
                  disabled={isProcessing}
                  className={`w-full max-w-md py-4 px-8 text-base btn-primary flex items-center justify-center space-x-3 ${
                    isProcessing ? 'opacity-75 cursor-not-allowed' : ''
                  }`}
                >
                  {isProcessing ? (
                    <>
                      <i className="fa-solid fa-circle-notch fa-spin text-xl"></i>
                      <span>Processing Data...</span>
                    </>
                  ) : (
                    <>
                      <i className="fa-solid fa-play text-lg"></i>
                      <span>Process & Export Data</span>
                    </>
                  )}
                </button>

                {processStatus && (
                  <div className="text-xs px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono text-center max-w-lg">
                    Status: {processStatus}
                  </div>
                )}

                {latestExportFilename && (
                  <div className="flex flex-col items-center space-y-2 pt-1 animate-fade-in">
                    <a
                      href={`/main-app/download-output/?file=${encodeURIComponent(latestExportFilename)}`}
                      download={latestExportFilename}
                      className="px-6 py-3.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl font-bold text-sm flex items-center space-x-3 shadow-xl shadow-emerald-600/30 transition-all border border-emerald-400/30 hover:scale-[1.02]"
                    >
                      <i className="fa-solid fa-cloud-arrow-down text-lg"></i>
                      <span>Download {latestExportFilename}</span>
                    </a>
                    <span className="text-[11px] text-gray-400 flex items-center space-x-1">
                      <i className="fa-solid fa-circle-check text-emerald-400 text-[10px]"></i>
                      <span>File automatically saved to your Downloads folder! Click above if you want to download again.</span>
                    </span>
                  </div>
                )}

                {catalogSyncInfo && (
                  <div className="w-full max-w-lg mt-3 p-3 rounded-xl bg-indigo-950/40 border border-indigo-500/30 flex items-center justify-between gap-3 animate-fade-in shadow-lg">
                    <div className="flex items-center space-x-2.5 min-w-0">
                      <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0 border border-indigo-500/30">
                        <i className="fa-solid fa-layer-group text-sm"></i>
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs font-semibold text-indigo-200 truncate flex items-center space-x-1.5">
                          <span>Product & SKU Catalog:</span>
                          <span className="text-white font-bold">{catalogSyncInfo.party_name}</span>
                        </div>
                        <div className="text-[11px] text-gray-400">
                          {catalogSyncInfo.added > 0 ? `${catalogSyncInfo.added} new added` : 'Already up-to-date'}
                          {catalogSyncInfo.updated > 0 ? `, ${catalogSyncInfo.updated} updated` : ''}
                          {catalogSyncInfo.skipped > 0 && catalogSyncInfo.added === 0 ? ` (${catalogSyncInfo.total} items synced)` : ''}
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => openCatalogForParty(catalogSyncInfo.party_id, catalogSyncInfo.party_name)}
                      className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center space-x-1.5 shrink-0 transition-all shadow-md shadow-indigo-600/30"
                      title="Open Product & SKU Catalog on same page"
                    >
                      <i className="fa-solid fa-arrow-up-right-from-square text-[11px]"></i>
                      <span>View Catalog</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {(activeTab === 'database' || activeTab === 'html_master') && (
            <div className="flex-1 flex flex-col min-h-0 space-y-4">

              {/* Sub-tab 1: Company Business Policies */}
              {activeTab === 'database' && dbSubTab === 'policies' && (
                <div className="space-y-6">
                  <div className="flex justify-between items-center">
                    <h3 className="text-base font-semibold text-gray-200">Registered Company Policies ({policies.length})</h3>
                    <button
                      onClick={() => setEditingPolicy({ company_name: '', shipping_profile_name: '', return_profile_name: '', payment_profile_name: '', brand_name: '', location: '' })}
                      className="btn-primary px-4 py-2 text-xs flex items-center space-x-2"
                    >
                      <i className="fa-solid fa-plus"></i>
                      <span>Add New Company Policy</span>
                    </button>
                  </div>

                  {/* Policies Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {policies.map(p => (
                      <div key={p.id} className="p-5 glass-card space-y-3 relative group">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-bold text-indigo-300 text-base">{p.company_name}</h4>
                            <div className="text-xs text-gray-400 mt-0.5">Brand: {p.brand_name || 'N/A'} | Location: {p.location || 'N/A'}</div>
                          </div>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => setEditingPolicy(p)}
                              className="p-2 text-xs rounded-lg bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20"
                              title="Edit Policy"
                            >
                              <i className="fa-solid fa-pen"></i>
                            </button>
                            {isAdminMode && (
                              <button
                                onClick={() => handleDeletePolicy(p.id)}
                                className="p-2 text-xs rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20"
                                title="Delete Policy"
                              >
                                <i className="fa-solid fa-trash"></i>
                              </button>
                            )}
                          </div>
                        </div>

                        <div className="text-xs space-y-1 pt-2 border-t border-white/5 text-gray-300">
                          <div><span className="text-gray-400">Shipping Profile:</span> {p.shipping_profile_name || 'None'}</div>
                          <div><span className="text-gray-400">Return Profile:</span> {p.return_profile_name || 'None'}</div>
                          <div><span className="text-gray-400">Payment Profile:</span> {p.payment_profile_name || 'None'}</div>
                        </div>

                        {/* Master Blueprint File Status & Actions */}
                        <div className="pt-2 border-t border-white/5 flex items-center justify-between text-xs">
                          <div className="flex items-center space-x-1.5 min-w-0">
                            {blueprintsMap[p.company_name.toLowerCase()] ? (
                              <>
                                <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)] shrink-0"></span>
                                <span className="text-emerald-300 truncate font-medium text-[11px]" title={`Blueprint: ${blueprintsMap[p.company_name.toLowerCase()].filename}`}>
                                  Blueprint: <span className="text-white font-semibold">{blueprintsMap[p.company_name.toLowerCase()].filename}</span> ({blueprintsMap[p.company_name.toLowerCase()].size_kb} KB)
                                </span>
                              </>
                            ) : (
                              <>
                                <span className="w-2 h-2 rounded-full bg-amber-400 shrink-0"></span>
                                <span className="text-amber-300 font-medium text-[11px]">No Blueprint Attached</span>
                              </>
                            )}
                          </div>
                          <div className="flex items-center space-x-1.5 shrink-0 ml-2">
                            <label className="cursor-pointer px-2 py-0.5 rounded bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-200 border border-indigo-400/30 font-semibold text-[11px] flex items-center space-x-1 transition-all" title="Upload or replace master blueprint (.xlsx)">
                              <i className="fa-solid fa-cloud-arrow-up text-[10px]"></i>
                              <span>{blueprintsMap[p.company_name.toLowerCase()] ? 'Replace' : 'Upload'}</span>
                              <input
                                type="file"
                                accept=".xlsx,.xls"
                                className="hidden"
                                onChange={(e) => {
                                  const f = e.target.files && e.target.files[0];
                                  if (f) handleUploadCompanyBlueprint(p.company_name, f);
                                  e.target.value = '';
                                }}
                              />
                            </label>
                            {blueprintsMap[p.company_name.toLowerCase()] && (
                              <a
                                href={`/main-app/download-output/?type=blueprint&company=${encodeURIComponent(p.company_name)}`}
                                download={`${p.company_name}.xlsx`}
                                className="p-1 px-1.5 rounded bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 text-[11px] transition-colors"
                                title="Download Current Master Blueprint Template"
                              >
                                <i className="fa-solid fa-download"></i>
                              </a>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Policy Edit Modal */}
                  {editingPolicy && (
                    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                      <div className="glass-card max-w-xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
                        <h3 className="text-lg font-bold text-white">
                          {editingPolicy.id ? 'Edit Company Policy' : 'Add New Company Policy'}
                        </h3>
                        <form onSubmit={handleSavePolicy} className="space-y-4">
                          <div>
                            <label className="block text-xs font-semibold text-gray-300 mb-1">Company Name</label>
                            <input
                              type="text"
                              value={editingPolicy.company_name}
                              onChange={(e) => setEditingPolicy({ ...editingPolicy, company_name: e.target.value })}
                              className="w-full glass-input px-3 py-2 text-sm"
                              required
                            />
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="block text-xs font-semibold text-gray-300 mb-1">Brand Name</label>
                              <input
                                type="text"
                                value={editingPolicy.brand_name || ''}
                                onChange={(e) => setEditingPolicy({ ...editingPolicy, brand_name: e.target.value })}
                                className="w-full glass-input px-3 py-2 text-sm"
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-semibold text-gray-300 mb-1">Location</label>
                              <input
                                type="text"
                                value={editingPolicy.location || ''}
                                onChange={(e) => setEditingPolicy({ ...editingPolicy, location: e.target.value })}
                                className="w-full glass-input px-3 py-2 text-sm"
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-3 gap-3">
                            <div>
                              <label className="block text-xs font-semibold text-gray-300 mb-1">Shipping Profile</label>
                              <input
                                type="text"
                                value={editingPolicy.shipping_profile_name || ''}
                                onChange={(e) => setEditingPolicy({ ...editingPolicy, shipping_profile_name: e.target.value })}
                                className="w-full glass-input px-3 py-2 text-sm"
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-semibold text-gray-300 mb-1">Return Profile</label>
                              <input
                                type="text"
                                value={editingPolicy.return_profile_name || ''}
                                onChange={(e) => setEditingPolicy({ ...editingPolicy, return_profile_name: e.target.value })}
                                className="w-full glass-input px-3 py-2 text-sm"
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-semibold text-gray-300 mb-1">Payment Profile</label>
                              <input
                                type="text"
                                value={editingPolicy.payment_profile_name || ''}
                                onChange={(e) => setEditingPolicy({ ...editingPolicy, payment_profile_name: e.target.value })}
                                className="w-full glass-input px-3 py-2 text-sm"
                              />
                            </div>
                          </div>

                          {/* Company Master Blueprint File Upload in Modal */}
                          <div className="p-3.5 rounded-xl bg-indigo-950/30 border border-indigo-500/20 space-y-2">
                            <label className="block text-xs font-semibold text-indigo-300 flex items-center justify-between">
                              <span className="flex items-center space-x-1.5">
                                <i className="fa-solid fa-file-excel text-emerald-400"></i>
                                <span>Master Blueprint Template (.xlsx)</span>
                              </span>
                              {editingPolicy.company_name && blueprintsMap[editingPolicy.company_name.toLowerCase()] && (
                                <span className="text-[10px] text-emerald-400 font-bold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                                  ✓ Attached ({blueprintsMap[editingPolicy.company_name.toLowerCase()].filename})
                                </span>
                              )}
                            </label>
                            <p className="text-[11px] text-gray-400">
                              Upload the master blank eBay template workbook for this company (saved to <code className="text-indigo-300">main/{editingPolicy.company_name || 'Company'}.xlsx</code>).
                            </p>
                            <div className="flex items-center justify-between pt-1">
                              <label className="cursor-pointer px-3.5 py-1.5 rounded-lg bg-indigo-600/40 hover:bg-indigo-600/60 text-indigo-200 border border-indigo-400/30 font-semibold text-xs flex items-center space-x-2 transition-all shadow-sm">
                                <i className="fa-solid fa-cloud-arrow-up text-xs"></i>
                                <span>{editingPolicy.company_name && blueprintsMap[editingPolicy.company_name.toLowerCase()] ? 'Replace Blueprint File' : 'Upload Blueprint File (.xlsx)'}</span>
                                <input
                                  type="file"
                                  accept=".xlsx,.xls"
                                  className="hidden"
                                  onChange={(e) => {
                                    const f = e.target.files && e.target.files[0];
                                    if (f) {
                                      if (editingPolicy.company_name && editingPolicy.company_name.trim()) {
                                        handleUploadCompanyBlueprint(editingPolicy.company_name, f);
                                      } else {
                                        showToast('Please enter Company Name first!', 'warning');
                                      }
                                    }
                                    e.target.value = '';
                                  }}
                                />
                              </label>
                              {editingPolicy.company_name && blueprintsMap[editingPolicy.company_name.toLowerCase()] && (
                                <a
                                  href={`/main-app/download-output/?type=blueprint&company=${encodeURIComponent(editingPolicy.company_name)}`}
                                  download={`${editingPolicy.company_name}.xlsx`}
                                  className="px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 text-xs flex items-center space-x-1.5 transition-colors"
                                  title="Download Current Blueprint File"
                                >
                                  <i className="fa-solid fa-download text-[11px]"></i>
                                  <span>Download Current</span>
                                </a>
                              )}
                            </div>
                          </div>

                          <div className="flex justify-end space-x-3 pt-4 border-t border-white/10">
                            <button
                              type="button"
                              onClick={() => setEditingPolicy(null)}
                              className="btn-secondary px-4 py-2 text-xs"
                            >
                              Cancel
                            </button>
                            <button
                              type="submit"
                              className="btn-primary px-5 py-2 text-xs font-semibold"
                            >
                              Save Policy to DB
                            </button>
                          </div>
                        </form>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Sub-tab 2: Title Templates Editor */}
              {activeTab === 'database' && dbSubTab === 'templates' && (
                <div className="space-y-6">
                  {/* Filters & Add button */}
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div className="flex items-center space-x-3">
                      <div>
                        <span className="text-xs text-gray-400 mr-2 font-semibold">Metal:</span>
                        <select
                          value={templateMetalFilter}
                          onChange={(e) => setTemplateMetalFilter(e.target.value)}
                          className="glass-input px-3 py-1.5 text-xs"
                        >
                          <option value="all" className="bg-gray-900">All Metals</option>
                          <option value="gold" className="bg-gray-900">Gold</option>
                          <option value="platinum" className="bg-gray-900">Platinum</option>
                        </select>
                      </div>

                      {/* Company Scope Filter */}
                      <div>
                        <span className="text-xs text-gray-400 mr-1 font-semibold">Company:</span>
                        <select
                          value={templateCompanyFilter}
                          onChange={(e) => setTemplateCompanyFilter(e.target.value)}
                          className="glass-input px-3 py-1.5 text-xs"
                        >
                          <option value="all" className="bg-gray-900">All Companies</option>
                          {companies.map((comp, idx) => (
                            <option key={idx} value={comp} className="bg-gray-900">{comp}</option>
                          ))}
                        </select>
                      </div>

                      {/* Dynamic Cascading Category Filter */}
                      <div>
                        <div className="flex items-center space-x-1">
                          <span className="text-xs text-gray-400 mr-1 font-semibold">Category:</span>
                          <select
                            value={templateCatFilter}
                            onChange={(e) => setTemplateCatFilter(e.target.value)}
                            className="glass-input px-3 py-1.5 text-xs"
                          >
                            <option value="all" className="bg-gray-900">All Categories</option>
                            {availableCategories.map((c, idx) => (
                              <option key={idx} value={c.name} className="bg-gray-900">{c.name}</option>
                            ))}
                          </select>
                          <button
                            onClick={() => setShowAddCatModal(true)}
                            className="px-2 py-1 text-xs rounded bg-indigo-500/20 hover:bg-indigo-500/40 text-indigo-300 border border-indigo-500/30 font-semibold"
                            title="Add New Category"
                          >
                            + New
                          </button>
                          {isAdminMode && templateCatFilter !== 'all' && (
                            <div className="flex items-center space-x-1 shrink-0">
                              <button
                                onClick={() => {
                                  const catObj = dbCategories.find(c => c.name.toLowerCase() === templateCatFilter.toLowerCase());
                                  if (catObj) handleEditCategoryInDb(catObj);
                                }}
                                className="px-2 py-1 text-xs rounded bg-indigo-500/20 hover:bg-indigo-500/40 text-indigo-300 border border-indigo-500/30 transition-colors"
                                title={`Rename category "${templateCatFilter}"`}
                              >
                                <i className="fa-solid fa-pen text-[10px]"></i>
                              </button>
                              <button
                                onClick={() => {
                                  const catObj = dbCategories.find(c => c.name.toLowerCase() === templateCatFilter.toLowerCase());
                                  if (catObj) handleDeleteCategoryFromDb(catObj.id);
                                }}
                                className="px-2 py-1 text-xs rounded bg-rose-500/20 hover:bg-rose-500/40 text-rose-300 border border-rose-500/30 transition-colors"
                                title={`Delete category "${templateCatFilter}" from DB`}
                              >
                                <i className="fa-solid fa-trash text-[10px]"></i>
                              </button>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Dynamic Cascading Setting Column Filter */}
                      <div>
                        <div className="flex items-center space-x-1">
                          <span className="text-xs text-gray-400 mr-1 font-semibold">Setting Column:</span>
                          <select
                            value={templateSettingFilter}
                            onChange={(e) => setTemplateSettingFilter(e.target.value)}
                            className="glass-input px-3 py-1.5 text-xs"
                          >
                            <option value="all" className="bg-gray-900">All Columns</option>
                            {availableSettingColumns.map((col, idx) => (
                              <option key={idx} value={col.name} className="bg-gray-900">{col.name}</option>
                            ))}
                          </select>
                          <button
                            onClick={() => setShowAddColModal(true)}
                            className="px-2 py-1 text-xs rounded bg-indigo-500/20 hover:bg-indigo-500/40 text-indigo-300 border border-indigo-500/30 font-semibold"
                            title="Add New Setting Column"
                          >
                            + New
                          </button>
                          {isAdminMode && templateSettingFilter !== 'all' && (
                            <button
                              onClick={() => {
                                const colObj = dbSettingColumns.find(c => c.name.toLowerCase() === templateSettingFilter.toLowerCase());
                                if (colObj) handleDeleteSettingColumnFromDb(colObj.id);
                              }}
                              className="px-2 py-1 text-xs rounded bg-rose-500/20 hover:bg-rose-500/40 text-rose-300 border border-rose-500/30"
                              title={`Delete column "${templateSettingFilter}" from DB`}
                            >
                              <i className="fa-solid fa-trash text-[10px]"></i>
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Auto Filter Toggle Badge */}
                      <button
                        onClick={() => setAutoFilterEmpty(!autoFilterEmpty)}
                        className={`px-2.5 py-1 text-xs font-semibold rounded-lg flex items-center space-x-1 border transition-all ${
                          autoFilterEmpty
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                            : 'bg-white/5 text-gray-400 border-white/10'
                        }`}
                        title="Toggle Auto-Filtering dropdowns to only show categories/columns with existing titles"
                      >
                        <i className={`fa-solid ${autoFilterEmpty ? 'fa-filter' : 'fa-filter-circle-xmark'}`}></i>
                        <span>{autoFilterEmpty ? 'Auto-Filter: ON' : 'Auto-Filter: OFF'}</span>
                      </button>
                    </div>

                    <button
                      onClick={() => setEditingTemplate({
                        metal_type: 'gold',
                        product_category: templateCatFilter !== 'all' ? templateCatFilter : (dbCategories[0] ? dbCategories[0].name : 'Engagement Ring'),
                        setting_column: templateSettingFilter !== 'all' ? templateSettingFilter : (dbSettingColumns[0] ? dbSettingColumns[0].name : 'Default'),
                        template_text: ''
                      })}
                      className="btn-primary px-4 py-2 text-xs flex items-center space-x-2"
                    >
                      <i className="fa-solid fa-plus"></i>
                      <span>Add Title Template</span>
                    </button>
                  </div>

                  {/* Templates List & Empty State Handling */}
                  <div className="space-y-3">
                    {filteredTemplates.length > 0 ? (
                      filteredTemplates.map(t => (
                        <div key={t.id} className="p-4 glass-card flex items-center justify-between space-x-4">
                          <div className="space-y-1 flex-1">
                            <div className="flex items-center space-x-2">
                              <span className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase ${
                                t.metal_type === 'gold' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-slate-500/20 text-slate-300 border border-slate-500/30'
                              }`}>
                                {t.metal_type}
                              </span>
                              <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-indigo-500/20 text-indigo-300">
                                {t.product_category}
                              </span>
                              <span className="text-xs text-gray-400 font-mono">[{t.setting_column}]</span>
                              <span className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                                !t.company_name || t.company_name.toLowerCase() === 'all'
                                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                                  : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              }`}>
                                {!t.company_name || t.company_name.toLowerCase() === 'all' ? '🌐 All Companies' : `🏢 ${t.company_name}`}
                              </span>
                            </div>
                            <div className="text-sm font-mono text-gray-100">{t.template_text}</div>
                          </div>

                          <div className="flex space-x-2">
                            <button
                              onClick={() => setEditingTemplate(t)}
                              className="p-2 text-xs rounded-lg bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20"
                            >
                              <i className="fa-solid fa-pen"></i>
                            </button>
                            {isAdminMode && (
                              <button
                                onClick={() => handleDeleteTemplate(t.id)}
                                className="p-2 text-xs rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20"
                              >
                                <i className="fa-solid fa-trash"></i>
                              </button>
                            )}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="p-8 glass-card text-center space-y-3 bg-indigo-950/20 border-indigo-500/20">
                        <i className="fa-solid fa-folder-open text-3xl text-indigo-400"></i>
                        <div className="text-sm font-bold text-gray-200">
                          No Title Templates found for Category: "{templateCatFilter}" & Setting Column: "{templateSettingFilter}"
                        </div>
                        <p className="text-xs text-gray-400">
                          Create a new title pattern for this category and column combination, or reset filters.
                        </p>
                        <div className="flex justify-center space-x-3 pt-2">
                          <button
                            onClick={() => setEditingTemplate({
                              metal_type: 'gold',
                              product_category: templateCatFilter !== 'all' ? templateCatFilter : 'Engagement Ring',
                              setting_column: templateSettingFilter !== 'all' ? templateSettingFilter : 'Default',
                              company_name: templateCompanyFilter !== 'all' ? templateCompanyFilter : 'All',
                              template_text: ''
                            })}
                            className="btn-primary px-4 py-2 text-xs"
                          >
                            + Create Title for {templateCatFilter !== 'all' ? templateCatFilter : 'Category'}
                          </button>
                          <button
                            onClick={() => { setTemplateCatFilter('all'); setTemplateSettingFilter('all'); setTemplateCompanyFilter('all'); }}
                            className="btn-secondary px-4 py-2 text-xs"
                          >
                            Reset Filters
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Title Template Edit / Add Modal */}
                  {editingTemplate && (
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
                      <div className="glass-card max-w-5xl w-[94vw] max-h-[92vh] overflow-y-auto p-7 space-y-5 border-indigo-500/40 shadow-2xl">
                        <div className="flex justify-between items-center pb-3 border-b border-white/10">
                          <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                            <i className="fa-solid fa-pen-to-square text-indigo-400"></i>
                            <span>{editingTemplate.id ? 'Edit Title Template' : 'Add New Title Template'}</span>
                          </h3>
                          <button type="button" onClick={() => setEditingTemplate(null)} className="text-gray-400 hover:text-white p-1">
                            <i className="fa-solid fa-xmark text-lg"></i>
                          </button>
                        </div>

                        <form onSubmit={handleSaveTemplate} className="space-y-5">
                          {/* Metal Type, Company Scope, Category, Setting Column Select Grid */}
                          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                            <div>
                              <label className="block text-xs font-bold text-gray-200 mb-1">Metal Type:</label>
                              <select
                                value={editingTemplate.metal_type || 'gold'}
                                onChange={(e) => setEditingTemplate({ ...editingTemplate, metal_type: e.target.value })}
                                className="w-full glass-input px-3 py-2 text-xs font-semibold"
                              >
                                <option value="gold" className="bg-gray-900">Gold</option>
                                <option value="platinum" className="bg-gray-900">Platinum</option>
                              </select>
                            </div>

                            <div>
                              <label className="block text-xs font-bold text-gray-200 mb-1">Company Scope:</label>
                              <select
                                value={editingTemplate.company_name || 'All'}
                                onChange={(e) => setEditingTemplate({ ...editingTemplate, company_name: e.target.value })}
                                className="w-full glass-input px-3 py-2 text-xs font-semibold truncate"
                              >
                                <option value="All" className="bg-gray-900">All Companies (Default)</option>
                                {companies.map((c, idx) => (
                                  <option key={idx} value={c} className="bg-gray-900">{c}</option>
                                ))}
                              </select>
                            </div>

                            <div>
                              <label className="block text-xs font-bold text-gray-200 mb-1">Category:</label>
                              <select
                                value={editingTemplate.product_category || 'Engagement Ring'}
                                onChange={(e) => setEditingTemplate({ ...editingTemplate, product_category: e.target.value })}
                                className="w-full glass-input px-3 py-2 text-xs font-semibold truncate"
                              >
                                {dbCategories.map((c, idx) => (
                                  <option key={idx} value={c.name} className="bg-gray-900">{c.name}</option>
                                ))}
                              </select>
                            </div>

                            <div>
                              <label className="block text-xs font-bold text-gray-200 mb-1">Setting Column:</label>
                              <select
                                value={editingTemplate.setting_column || 'Default'}
                                onChange={(e) => setEditingTemplate({ ...editingTemplate, setting_column: e.target.value })}
                                className="w-full glass-input px-3 py-2 text-xs font-semibold truncate"
                              >
                                {getSettingColumnsForCategory(editingTemplate.product_category || 'Engagement Ring', dbSettingColumns, templates).map((col, idx) => (
                                  <option key={idx} value={col.name} className="bg-gray-900">{col.name}</option>
                                ))}
                              </select>
                            </div>
                          </div>

                          {/* Template Text Area & Quick Variable Tag Palette */}
                          <div className="space-y-2">
                            <div className="flex justify-between items-center">
                              <label className="block text-xs font-semibold text-gray-300">Title Template Pattern:</label>
                              <select
                                onChange={(e) => {
                                  if (!e.target.value) return;
                                  handleInsertTagToTitleTemplate(e.target.value);
                                  e.target.value = '';
                                }}
                                className="bg-black/70 border border-purple-500/40 text-xs text-indigo-300 rounded px-2 py-0.5 focus:outline-none"
                              >
                                <option value="">+ Select Tag...</option>
                                {placeholders.map(p => (
                                  <option key={p.name} value={p.name}>{formatTag(p.name)}</option>
                                ))}
                              </select>
                            </div>

                            {/* Quick Clickable Variable Tag Pills Palette with Add & Remove */}
                            <div className="space-y-2 p-3 bg-black/50 rounded-xl border border-purple-500/30 shadow-inner">
                              <div className="flex justify-between items-center">
                                <div className="text-[11px] text-purple-300 font-semibold flex items-center space-x-1.5">
                                  <i className="fa-solid fa-bolt text-amber-400"></i>
                                  <span>Quick Click Variable Tags (click tag to insert):</span>
                                </div>
                                <button
                                  type="button"
                                  onClick={() => setShowAddPlaceholderInput(!showAddPlaceholderInput)}
                                  className="px-2 py-0.5 text-[11px] rounded bg-purple-500/20 hover:bg-purple-500/40 text-purple-300 border border-purple-500/40 font-semibold flex items-center space-x-1 transition-all"
                                  title="Add new custom variable tag"
                                >
                                  <i className="fa-solid fa-plus text-[10px]"></i>
                                  <span>Add Tag</span>
                                </button>
                              </div>

                              {showAddPlaceholderInput && (
                                <div className="flex space-x-2 py-1">
                                  <input
                                    type="text"
                                    placeholder="Tag name e.g. {SIDE_STONE_SHAPE}"
                                    value={newPlaceholderName}
                                    onChange={(e) => setNewPlaceholderName(e.target.value)}
                                    className="flex-1 glass-input px-3 py-1 text-xs font-mono"
                                    autoFocus
                                  />
                                  <button
                                    type="button"
                                    onClick={handleAddPlaceholderToDb}
                                    className="btn-primary px-3 py-1 text-xs font-semibold"
                                  >
                                    Save Tag
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => setShowAddPlaceholderInput(false)}
                                    className="btn-secondary px-2 py-1 text-xs"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              )}

                              <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto pt-0.5">
                                {placeholders.map(p => {
                                  const tagStr = formatTag(p.name);
                                  return (
                                    <div
                                      key={p.id || p.name}
                                      onMouseDown={(e) => { e.preventDefault(); handleInsertTagToTitleTemplate(p.name); }}
                                      className="inline-flex items-center space-x-1 px-2.5 py-1 text-[11px] font-mono rounded-lg bg-indigo-500/20 hover:bg-indigo-500/35 text-indigo-200 border border-indigo-500/40 font-semibold transition-all group cursor-pointer"
                                    >
                                      <button
                                        type="button"
                                        className="flex items-center space-x-1 cursor-pointer hover:text-white"
                                        title={`Click to replace selection or insert ${tagStr}`}
                                      >
                                        <span className="text-amber-400 font-bold">+</span>
                                        <span>{tagStr}</span>
                                      </button>
                                      <button
                                        type="button"
                                        onClick={(e) => handleDeletePlaceholderFromDb(p.id, e)}
                                        className="text-gray-400 hover:text-rose-400 transition-colors ml-1 p-0.5 rounded hover:bg-rose-500/20"
                                        title={`Remove tag ${tagStr}`}
                                      >
                                        <i className="fa-solid fa-xmark text-[10px]"></i>
                                      </button>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>


                            <textarea
                              ref={titleTextareaRef}
                              rows={4}
                              value={(editingTemplate.template_text || '').replace(/\{\{/g, '{').replace(/\}\}/g, '}')}
                              onChange={(e) => {
                                handleTitleTextareaSelect(e);
                                setEditingTemplate({ ...editingTemplate, template_text: e.target.value.replace(/\{\{/g, '{').replace(/\}\}/g, '}') });
                              }}
                              onSelect={handleTitleTextareaSelect}
                              onKeyUp={handleTitleTextareaSelect}
                              onMouseUp={handleTitleTextareaSelect}
                              onFocus={handleTitleTextareaSelect}
                              placeholder="e.g. {TCW}ct {CERTI_BY} Lab Grown Diamond Engagement Ring {CENTER_STONE_SHAPE} {GOLD_KT} {GOLD_COLOR} Gold"
                              className="w-full glass-input p-3.5 text-sm font-mono text-indigo-200 border-indigo-500/30 focus:border-indigo-400 leading-relaxed shadow-inner"
                              required
                            ></textarea>

                          </div>

                          <div className="flex justify-end space-x-3 pt-3 border-t border-white/10">
                            <button
                              type="button"
                              onClick={() => setEditingTemplate(null)}
                              className="btn-secondary px-4 py-2 text-xs"
                            >
                              Cancel
                            </button>
                            <button
                              type="submit"
                              className="btn-primary px-5 py-2 text-xs font-semibold flex items-center space-x-2"
                            >
                              <i className="fa-solid fa-floppy-disk"></i>
                              <span>Save Title Template</span>
                            </button>
                          </div>
                        </form>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {(activeTab === 'html_master' || (activeTab === 'database' && dbSubTab === 'html_templates')) && (
                <div className="flex-1 flex flex-col min-h-0 space-y-3">

                  {activeTab === 'html_master' && (
                    <div className="flex items-center justify-between p-2 glass-card bg-black/40 border border-white/10 rounded-xl shrink-0">
                      <div className="flex items-center space-x-2">
                        <button
                          type="button"
                          onClick={() => setHtmlAppMode('integrated')}
                          className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center space-x-2 ${
                            htmlAppMode === 'integrated'
                              ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-500/25 border border-purple-400/40'
                              : 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 border border-white/5'
                          }`}
                        >
                          <i className="fa-solid fa-code text-xs"></i>
                          <span>⚡ Integrated Studio</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => setHtmlAppMode('standalone_html_app')}
                          className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center space-x-2 ${
                            htmlAppMode === 'standalone_html_app'
                              ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-md shadow-emerald-500/25 border border-emerald-400/40'
                              : 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 border border-white/5'
                          }`}
                        >
                          <i className="fa-solid fa-window-maximize text-xs"></i>
                          <span>🚀 Standalone HTML App (Original View)</span>
                        </button>
                      </div>

                      {/* Hidden File Input for Excel Import */}
                      <input
                        type="file"
                        ref={fileInputRefHtmlExcel}
                        onChange={handleImportHtmlExcelChange}
                        accept=".xlsx, .xls"
                        className="hidden"
                      />

                      <div className="flex items-center space-x-2">
                        <button
                          type="button"
                          onClick={() => fileInputRefHtmlExcel.current?.click()}
                          className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 border border-emerald-500/40 transition-all flex items-center space-x-1.5 shadow-sm"
                          title="Import & Bulk Add/Update HTML templates from Excel (.xlsx) file"
                        >
                          <i className="fa-solid fa-file-excel text-xs text-emerald-400"></i>
                          <span>📤 Import Excel</span>
                        </button>

                        <button
                          type="button"
                          onClick={handleExportHtmlTemplatesToExcel}
                          className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/40 transition-all flex items-center space-x-1.5 shadow-sm"
                          title="Export all saved HTML templates to Excel (.xlsx) file"
                        >
                          <i className="fa-solid fa-file-export text-xs text-indigo-400"></i>
                          <span>📥 Export Excel</span>
                        </button>

                        <button
                          type="button"
                          onClick={handleDownloadSampleHtmlExcel}
                          className="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 transition-all flex items-center space-x-1.5"
                          title="Download sample Excel template format for bulk HTML import"
                        >
                          <i className="fa-solid fa-circle-question text-xs text-amber-400"></i>
                          <span>Sample Excel</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => {
                            callEel('open_floating_widget').catch(err => console.error(err));
                          }}
                          className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-teal-600/20 hover:bg-teal-600/40 text-teal-300 border border-teal-500/40 transition-all flex items-center space-x-1.5 shadow-sm"
                          title="Open On-Top Floating Quick Action Widget"
                        >
                          <i className="fa-solid fa-window-restore text-xs"></i>
                          <span>Quick Widget</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {activeTab === 'html_master' && htmlAppMode === 'standalone_html_app' ? (
                    <div className="flex-1 w-full h-full min-h-0 rounded-xl overflow-hidden glass-card border border-white/10 shadow-2xl">
                      <iframe
                        src="html_app_modify.html"
                        className="w-full h-full border-0"
                        title="Standalone eBay HTML App"
                      />
                    </div>
                  ) : (
                    <React.Fragment>
                    {/* HTML Code Editor & Live Preview Layout (Resizable Splitters) */}
                    <div ref={mainGridContainerRef} className="flex flex-col lg:flex-row flex-1 min-h-0 relative select-none" style={{ gap: '0px' }}>
                    
                    {/* Transparent Dragging Overlay (Prevents Iframe Event Hijacking) */}
                    {(isResizingPaneSplit || isResizingEditorSplit) && (
                      <div className={`absolute inset-0 z-50 ${isResizingPaneSplit ? 'cursor-col-resize' : 'cursor-row-resize'}`} />
                    )}

                    {/* Left Pane: Code Textarea & Tag Palette (Resizable Vertically) */}
                    <div 
                      ref={leftPaneContainerRef}
                      className="flex flex-col min-h-0 h-full relative"
                      style={{ width: showLivePreview ? `${paneSplitRatio}%` : '100%', minWidth: showLivePreview ? '220px' : '100%' }}
                    >
                      {/* Top Div: Code Textarea (Dynamic Height / Flex-1 Default) */}
                      <div 
                        className={`space-y-2 flex flex-col min-h-0 ${editorSplitRatio !== null ? '' : 'flex-1'}`}
                        style={editorSplitRatio !== null ? { height: `${editorSplitRatio}%`, minHeight: '100px' } : { minHeight: '150px' }}
                      >
                        <div className="flex justify-between items-center shrink-0">
                          <label className="text-xs font-semibold text-gray-300 flex items-center space-x-2">
                            <i className="fa-solid fa-code text-indigo-400"></i>
                            <span>HTML Listing Code ({selectedHtmlCompany} &mdash; {selectedHtmlCategory} / {selectedHtmlSubcategory})</span>
                          </label>

                          <div className="flex items-center space-x-2">
                            <button
                              type="button"
                              onClick={() => {
                                callEel('open_floating_widget').catch(err => console.error(err));
                              }}
                              className="px-2.5 py-1 text-xs font-semibold rounded-lg border bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 border-emerald-500/30 transition-all flex items-center space-x-1.5 shadow-sm"
                              title="Open On-Top Floating Quick Action Widget"
                            >
                              <i className="fa-solid fa-window-restore text-[11px]"></i>
                              <span>Quick Widget</span>
                            </button>

                            <button
                              type="button"
                              onClick={() => setShowFindReplaceBar(!showFindReplaceBar)}
                              className={`px-2.5 py-1 text-xs font-semibold rounded-lg border transition-all flex items-center space-x-1.5 ${
                                showFindReplaceBar
                                  ? 'bg-indigo-600 text-white border-indigo-400 shadow-md'
                                  : 'bg-white/5 hover:bg-white/10 text-indigo-300 border-white/10'
                              }`}
                              title="Toggle Find & Replace Bar (Ctrl+F)"
                            >
                              <i className="fa-solid fa-magnifying-glass-arrow-right text-[11px]"></i>
                              <span>Find & Replace</span>
                            </button>
                            <span className="text-xs text-gray-400 font-mono hidden sm:inline">Highlight text & click tag to replace</span>
                          </div>
                        </div>

                        {/* Expandable Find & Replace Tool Panel (Dedicated 100% Full Width Rows) */}
                        {showFindReplaceBar && (
                          <div className="p-3.5 rounded-xl bg-slate-900/95 border border-indigo-500/40 shadow-2xl space-y-2.5 animate-fadeIn shrink-0 z-30">
                            {/* Row 1: Dedicated 100% Full-Width Find Textarea (Resizable Height) */}
                            <div className="flex items-center space-x-2 w-full">
                              <div className="relative flex-1 w-full">
                                <textarea
                                  rows={1}
                                  value={findSearchText}
                                  onChange={(e) => setFindSearchText(e.target.value)}
                                  placeholder="Find in HTML code (e.g. ITEM SPECIFICS)..."
                                  className="w-full glass-input pl-8 pr-28 py-2 text-xs text-indigo-100 font-mono focus:border-indigo-400 min-h-[38px] resize-y leading-relaxed"
                                  autoFocus
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                      e.preventDefault();
                                      handleReplaceNext();
                                    }
                                  }}
                                ></textarea>
                                <i className="fa-solid fa-magnifying-glass absolute left-2.5 top-3 text-indigo-400 text-xs pointer-events-none"></i>
                                
                                {findSearchText && (
                                  <span className={`absolute right-3 top-2 text-[11px] font-mono font-bold px-2 py-0.5 rounded pointer-events-none ${
                                    findMatchCount > 0 ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                                  }`}>
                                    {findMatchCount > 0 ? `${findMatchCount} match(es)` : '0 matches'}
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Row 2: Dedicated 100% Full-Width Replace Textarea (Resizable Height) */}
                            <div className="flex items-center space-x-2 w-full">
                              <div className="relative flex-1 w-full">
                                <textarea
                                  rows={1}
                                  value={replaceWithText}
                                  onChange={(e) => setReplaceWithText(e.target.value)}
                                  placeholder="Replace with text or tag (e.g. {ITEM_SPECIFICS})..."
                                  className="w-full glass-input pl-8 pr-3 py-2 text-xs text-purple-200 font-mono focus:border-purple-400 min-h-[38px] resize-y leading-relaxed"
                                ></textarea>
                                <i className="fa-solid fa-pen absolute left-2.5 top-3 text-purple-400 text-xs pointer-events-none"></i>
                              </div>
                            </div>

                            {/* Row 3: Action Buttons & Controls Row */}
                            <div className="flex flex-wrap items-center justify-between gap-2 w-full pt-1 border-t border-white/5">
                              <div className="flex items-center space-x-2">
                                {/* Tag Selection Dropdown for Replace Value */}
                                <select
                                  onChange={(e) => {
                                    if (e.target.value) {
                                      setReplaceWithText(e.target.value);
                                      e.target.value = '';
                                    }
                                  }}
                                  className="bg-black/80 border border-purple-500/40 text-xs text-amber-300 rounded-lg px-2.5 py-1.5 focus:outline-none font-semibold cursor-pointer shrink-0"
                                  title="Set replacement value from placeholder tag"
                                >
                                  <option value="">+ Insert Tag...</option>
                                  {placeholders.map(p => (
                                    <option key={p.name} value={p.name}>{formatTag(p.name)}</option>
                                  ))}
                                </select>

                                {/* Case Sensitivity Toggle Button */}
                                <button
                                  type="button"
                                  onClick={() => setIsCaseSensitive(!isCaseSensitive)}
                                  className={`px-2.5 py-1.5 text-xs font-mono font-bold rounded-lg border transition-all shrink-0 ${
                                    isCaseSensitive
                                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/50'
                                      : 'bg-white/5 text-gray-400 border-white/10 hover:text-white'
                                  }`}
                                  title={isCaseSensitive ? 'Case Sensitive: ON' : 'Case Sensitive: OFF (Click to toggle)'}
                                >
                                  Aa
                                </button>
                              </div>

                              <div className="flex items-center space-x-2">
                                {/* Replace Button */}
                                <button
                                  type="button"
                                  onClick={handleReplaceNext}
                                  className="px-3.5 py-1.5 text-xs font-bold btn-secondary hover:bg-indigo-600 hover:text-white flex items-center space-x-1.5 shrink-0"
                                >
                                  <i className="fa-solid fa-play text-[10px]"></i>
                                  <span>Replace</span>
                                </button>

                                {/* Replace All Button */}
                                <button
                                  type="button"
                                  onClick={handleReplaceAll}
                                  className="px-4 py-1.5 text-xs font-bold btn-primary bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 flex items-center space-x-1.5 shadow-md shrink-0"
                                >
                                  <i className="fa-solid fa-arrows-rotate text-[10px]"></i>
                                  <span>Replace All</span>
                                </button>

                                {/* Close Panel Button */}
                                <button
                                  type="button"
                                  onClick={() => setShowFindReplaceBar(false)}
                                  className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-white/10 text-xs shrink-0"
                                  title="Close Find & Replace"
                                >
                                  <i className="fa-solid fa-xmark text-sm"></i>
                                </button>
                              </div>
                            </div>
                          </div>
                        )}

                        <textarea
                          ref={htmlEditorTextareaRef}
                          value={currentHtmlText}
                          onChange={(e) => setCurrentHtmlText(e.target.value)}
                          onSelect={handleHtmlTextareaSelect}
                          onKeyUp={handleHtmlTextareaSelect}
                          onMouseUp={handleHtmlTextareaSelect}
                          onKeyDown={(e) => {
                            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                              e.preventDefault();
                              setShowFindReplaceBar(true);
                            }
                          }}
                          placeholder={`Paste or edit HTML listing code for ${selectedHtmlCompany} (${selectedHtmlCategory} / ${selectedHtmlSubcategory})...`}
                          className="w-full glass-input p-4 text-xs font-mono leading-relaxed focus:ring-2 focus:ring-indigo-500 flex-1 h-full resize-none"
                        ></textarea>
                      </div>

                      {/* Vertical Drag Handle Splitter (Top Textarea vs Bottom Tags) */}
                      <div
                        onMouseDown={(e) => { e.preventDefault(); setIsResizingEditorSplit(true); }}
                        className={`h-3 cursor-row-resize flex items-center justify-center my-1 group transition-all rounded select-none z-20 ${
                          isResizingEditorSplit ? 'bg-purple-600/40' : 'hover:bg-purple-500/20'
                        }`}
                        title="Drag up/down to resize Code Textarea vs Tag Palette"
                      >
                        <div className={`h-1 w-20 rounded-full transition-all ${
                          isResizingEditorSplit ? 'bg-purple-400 shadow-[0_0_12px_rgba(192,132,252,0.8)] scale-y-125' : 'bg-white/25 group-hover:bg-purple-400'
                        }`} />
                      </div>

                      {/* Bottom Div: HTML Helper Tag Badges & Live Selection Banner (Auto Content Height) */}
                      <div 
                        className={`p-3 glass-card bg-indigo-950/20 border-indigo-500/20 space-y-2 overflow-y-auto ${
                          editorSplitRatio !== null ? 'flex-1 min-h-0' : 'h-auto shrink-0 max-h-[50%]'
                        }`}
                        style={editorSplitRatio !== null ? { height: `${100 - editorSplitRatio}%`, minHeight: '80px' } : {}}
                      >
                        {previewSelectedText && (
                          <div className="p-3 rounded-xl bg-purple-950/80 border border-purple-500/50 shadow-2xl space-y-2.5 animate-fadeIn">
                            <div className="flex items-center justify-between border-b border-purple-500/30 pb-2">
                              <div className="flex items-center space-x-2 text-xs text-purple-200 font-semibold">
                                <i className="fa-solid fa-pen-to-square text-purple-400 text-sm"></i>
                                <span>Edit Highlighted Preview Text:</span>
                                <code className="bg-black/60 px-2 py-0.5 rounded font-mono text-amber-300 border border-amber-500/30 font-bold max-w-[200px] truncate">
                                  "{previewSelectedText}"
                                </code>
                              </div>

                              <button
                                type="button"
                                onClick={() => { setPreviewSelectedText(''); setReplacementTextInput(''); }}
                                className="text-xs text-gray-400 hover:text-white px-2 py-0.5 rounded bg-white/10"
                              >
                                <i className="fa-solid fa-xmark mr-1"></i>
                                Cancel
                              </button>
                            </div>

                            <form onSubmit={(e) => { e.preventDefault(); handleReplaceSelectedPreviewText(replacementTextInput); }} className="flex flex-wrap items-center gap-2">
                              <div className="flex-1 min-w-[200px]">
                                <input
                                  type="text"
                                  value={replacementTextInput}
                                  onChange={(e) => setReplacementTextInput(e.target.value)}
                                  placeholder={`Type new text to replace "${previewSelectedText}"...`}
                                  className="w-full glass-input px-3 py-1.5 text-xs text-indigo-100 font-semibold focus:border-purple-400"
                                  autoFocus
                                />
                              </div>

                              <button
                                type="submit"
                                className="btn-primary px-3.5 py-1.5 text-xs font-bold flex items-center space-x-1.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 shadow-md"
                              >
                                <i className="fa-solid fa-check"></i>
                                <span>Replace in HTML Code</span>
                              </button>

                              <select
                                onChange={(e) => {
                                  if (!e.target.value) return;
                                  handleReplaceSelectedPreviewText(formatTag(e.target.value));
                                  e.target.value = '';
                                }}
                                className="bg-black/80 border border-purple-500/50 text-xs text-amber-300 rounded-xl px-3 py-1.5 focus:outline-none font-semibold cursor-pointer"
                              >
                                <option value="">+ Replace with Tag...</option>
                                {placeholders.map(p => (
                                  <option key={p.name} value={p.name}>{formatTag(p.name)}</option>
                                ))}
                              </select>
                            </form>
                          </div>
                        )}

                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-semibold text-indigo-300">
                            {previewSelectedText ? `Click any tag below to replace "${previewSelectedText}" in HTML code:` : 'Highlight text in Live Preview OR code textarea & click tag to replace:'}
                          </span>

                          <button
                            type="button"
                            onClick={() => setShowAddPlaceholderInput(!showAddPlaceholderInput)}
                            className="text-[11px] text-indigo-400 hover:text-indigo-300 font-semibold flex items-center space-x-1"
                          >
                            <i className="fa-solid fa-plus"></i>
                            <span>Add New Tag</span>
                          </button>
                        </div>

                        {/* Add Placeholder Form */}
                        {showAddPlaceholderInput && (
                          <div className="flex space-x-2 py-1">
                            <input
                              type="text"
                              placeholder="Tag name e.g. {ITEM_LENGTH}"
                              value={newPlaceholderName}
                              onChange={(e) => setNewPlaceholderName(e.target.value)}
                              className="flex-1 glass-input px-3 py-1 text-xs"
                            />
                            <button
                              type="button"
                              onClick={handleAddPlaceholderToDb}
                              className="btn-primary px-3 py-1 text-xs"
                            >
                              Save Tag
                            </button>
                          </div>
                        )}

                        {/* Interactive Placeholders with Focus-Preserving onMouseDown */}
                        <div className="flex flex-wrap gap-1.5">
                          {placeholders.map((p) => (
                            <div
                              key={p.id}
                              className="inline-flex items-center space-x-1 px-2 py-0.5 text-[11px] font-mono bg-white/5 hover:bg-indigo-500/40 border border-white/10 hover:border-indigo-400/50 rounded text-indigo-200 transition-all hover:scale-105 group"
                            >
                              <span
                                onMouseDown={(e) => { e.preventDefault(); handleInsertHtmlTag(p.name); }}
                                className="cursor-pointer hover:text-white font-bold"
                                title={`Click to replace selected text with ${p.name}`}
                              >
                                {p.name}
                              </span>
                              <button
                                type="button"
                                onMouseDown={(e) => { e.stopPropagation(); e.preventDefault(); }}
                                onClick={(e) => {
                                  if (e) { e.stopPropagation(); e.preventDefault(); }
                                  handleEditPlaceholderInDb(p, e);
                                }}
                                className="text-gray-400 hover:text-indigo-300 transition-colors ml-1 p-0.5 rounded"
                                title="Rename tag"
                              >
                                <i className="fa-solid fa-pen text-[9px]"></i>
                              </button>
                              <button
                                type="button"
                                onMouseDown={(e) => { e.stopPropagation(); e.preventDefault(); }}
                                onClick={(e) => {
                                  if (e) { e.stopPropagation(); e.preventDefault(); }
                                  handleDeletePlaceholderFromDb(p.id, e);
                                }}
                                className="text-gray-400 hover:text-rose-400 transition-colors p-0.5 rounded ml-0.5 hover:bg-rose-500/20"
                                title={`Delete tag ${p.name}`}
                              >
                                <i className="fa-solid fa-xmark text-[10px]"></i>
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Horizontal Drag Handle Splitter (Left Pane vs Right Preview) */}
                    {showLivePreview && (
                      <div
                        onMouseDown={(e) => { e.preventDefault(); setIsResizingPaneSplit(true); }}
                        className={`w-3.5 hover:w-3.5 cursor-col-resize flex items-center justify-center group transition-all select-none z-20 mx-1 ${
                          isResizingPaneSplit ? 'bg-indigo-600/40' : 'hover:bg-indigo-500/20'
                        }`}
                        title="Drag left/right to resize Code Editor vs Preview window"
                      >
                        <div className={`w-1 h-16 rounded-full transition-all ${
                          isResizingPaneSplit ? 'bg-indigo-400 shadow-[0_0_12px_rgba(129,140,248,0.8)] scale-x-125' : 'bg-white/25 group-hover:bg-indigo-400'
                        }`} />
                      </div>
                    )}

                    {/* Right Pane: Live Rendered Iframe Preview */}
                    {showLivePreview && (
                      <div 
                        className="space-y-2 flex flex-col min-h-0 h-full"
                        style={{ width: `${100 - paneSplitRatio}%`, minWidth: '220px' }}
                      >
                        <div className="flex justify-between items-center shrink-0">
                          <span className="text-xs font-semibold text-emerald-400 flex items-center space-x-2">
                            <i className="fa-solid fa-eye"></i>
                            <span>Live Real-Time Preview {isVisualEditing ? '(Visual Inspector Mode Active)' : ''}</span>
                          </span>

                          {/* Mode Toggle Bar & Detachable Pop-out Window Controls */}
                          <div className="flex items-center space-x-2">
                            {isPreviewDetached && (
                              <div className="flex items-center space-x-1 px-2 py-0.5 bg-amber-500/10 border border-amber-500/30 rounded-lg text-[11px] text-amber-300">
                                <i className="fa-solid fa-up-right-from-square text-[9px] animate-pulse"></i>
                                <span>Detached</span>
                                <button
                                  type="button"
                                  onClick={handleOpenDetachedWindow}
                                  className="px-1.5 py-0.5 bg-amber-500/20 hover:bg-amber-500/40 rounded text-[10px] font-bold underline"
                                  title="Focus detached window"
                                >
                                  Focus
                                </button>
                                <button
                                  type="button"
                                  onClick={handleCloseDetachedWindow}
                                  className="px-1.5 py-0.5 bg-white/10 hover:bg-rose-600 text-white rounded text-[10px] font-bold"
                                  title="Close separate window and dock back"
                                >
                                  Dock
                                </button>
                              </div>
                            )}

                            {/* Desktop vs Mobile View Mode Segmented Control */}
                            <div className="flex items-center space-x-1 p-0.5 rounded-lg bg-black/40 border border-white/10">
                              <button
                                type="button"
                                onClick={() => setPreviewDeviceMode('desktop')}
                                className={`px-2.5 py-1 text-[11px] font-semibold rounded flex items-center space-x-1 transition-all ${
                                  previewDeviceMode === 'desktop'
                                    ? 'bg-indigo-600 text-white shadow-sm'
                                    : 'text-gray-400 hover:text-white'
                                }`}
                                title="Desktop Full-Width View"
                              >
                                <i className="fa-solid fa-desktop text-[10px]"></i>
                                <span>Desktop</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => setPreviewDeviceMode('mobile')}
                                className={`px-2.5 py-1 text-[11px] font-semibold rounded flex items-center space-x-1 transition-all ${
                                  previewDeviceMode === 'mobile'
                                    ? 'bg-indigo-600 text-white shadow-sm'
                                    : 'text-gray-400 hover:text-white'
                                }`}
                                title="Mobile Responsive Viewport (380px)"
                              >
                                <i className="fa-solid fa-mobile-screen-button text-[10px]"></i>
                                <span>Mobile</span>
                              </button>
                            </div>

                            <div className="flex items-center space-x-1 p-0.5 rounded-lg bg-black/40 border border-white/10">
                              <button
                                onClick={() => setPreviewDataMode('raw')}
                                className={`px-2.5 py-1 text-[11px] font-semibold rounded transition-all ${
                                  previewDataMode === 'raw'
                                    ? 'bg-indigo-600 text-white shadow-sm'
                                    : 'text-gray-400 hover:text-white'
                                }`}
                              >
                                Raw Placeholders
                              </button>
                              <button
                                onClick={() => setPreviewDataMode('sample')}
                                className={`px-2.5 py-1 text-[11px] font-semibold rounded transition-all ${
                                  previewDataMode === 'sample'
                                    ? 'bg-indigo-600 text-white shadow-sm'
                                    : 'text-gray-400 hover:text-white'
                                }`}
                              >
                                Sample Data
                              </button>
                            </div>

                            <button
                              type="button"
                              onClick={handleOpenDetachedWindow}
                              className={`px-3 py-1 text-[11px] font-bold rounded-lg border transition-all flex items-center space-x-1.5 shadow-md ${
                                isPreviewDetached
                                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30'
                                  : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white border-purple-500/30'
                              }`}
                              title="Detach live preview into a separate resizable window for multi-monitor side-by-side editing"
                            >
                              <i className="fa-solid fa-up-right-from-square text-[10px]"></i>
                              <span>{isPreviewDetached ? 'Refocus Pop-out Window' : 'Pop-out Window'}</span>
                            </button>
                          </div>
                        </div>

                        {/* Live Rendered Viewport Frame: Desktop vs Mobile */}
                        <div className={`w-full flex-1 min-h-0 flex justify-center items-center rounded-xl border border-white/10 transition-all ${
                          previewDeviceMode === 'mobile'
                            ? 'bg-slate-950/80 p-4 min-h-[500px]'
                            : 'bg-white overflow-hidden shadow-2xl h-full'
                        }`}>
                          <div className={`transition-all duration-300 ${
                            previewDeviceMode === 'mobile'
                              ? 'w-[380px] h-[98%] max-h-[640px] border-[10px] border-slate-800 rounded-[36px] shadow-2xl overflow-hidden bg-white relative ring-1 ring-white/20 flex flex-col'
                              : 'w-full h-full'
                          }`}>
                            {previewDeviceMode === 'mobile' && (
                              <div className="w-full bg-slate-800 text-slate-300 py-1.5 px-3 text-[11px] font-mono font-bold border-b border-slate-700 flex justify-between items-center select-none">
                                <span className="flex items-center space-x-1.5 text-indigo-300">
                                  <i className="fa-solid fa-mobile-screen-button text-[10px]"></i>
                                  <span>Mobile (380px)</span>
                                </span>
                                <span className="text-[10px] text-slate-400">Preview</span>
                              </div>
                            )}
                            <iframe
                              ref={previewIframeRef}
                              title="Live Listing Preview"
                              srcDoc={renderLivePreviewHtml(currentHtmlText, previewDataMode, isVisualEditing)}
                              className="w-full h-full border-0 flex-1"
                              sandbox="allow-scripts allow-same-origin"
                            ></iframe>
                          </div>
                        </div>

                        {/* DevTools Inspect Element & Live Editor Panel */}
                        {isVisualEditing && (
                          <div className="p-3.5 bg-slate-900/95 border border-purple-500/40 rounded-xl space-y-3 shadow-2xl backdrop-blur-md animate-fade-in text-gray-200">
                            {inspectedElement ? (
                              <>
                                {/* Header / Breadcrumb Bar */}
                                <div className="flex items-center justify-between pb-2.5 border-b border-white/10 text-xs">
                                  <div className="flex items-center space-x-2">
                                    <span className="px-2 py-0.5 bg-purple-600 text-white font-mono font-bold rounded shadow-sm">
                                      {inspectedElement.tagName}
                                    </span>
                                    <span className="font-mono text-purple-300 font-semibold truncate max-w-[240px]">
                                      {inspectedElement.id ? `#${inspectedElement.id}` : ''}
                                      {inspectedElement.className ? `.${inspectedElement.className.split(' ').join('.')}` : ''}
                                    </span>
                                  </div>

                                  <div className="flex items-center space-x-2">
                                    <button
                                      type="button"
                                      onClick={() => {
                                        setIsVisualEditing(false);
                                        setInspectedElement(null);
                                      }}
                                      className="px-2.5 py-1 text-[11px] font-semibold bg-purple-500/20 hover:bg-purple-500/40 text-purple-200 rounded flex items-center space-x-1 border border-purple-500/30 transition-all"
                                      title="Turn Off Visual Inspector Mode"
                                    >
                                      <i className="fa-solid fa-eye-slash text-[10px]"></i>
                                      <span>Visual OFF</span>
                                    </button>

                                    <button
                                      type="button"
                                      onClick={() => postToIframe({ type: 'EXEC_INSPECT_PARENT' })}
                                      className="px-2.5 py-1 text-[11px] font-semibold bg-white/10 hover:bg-white/20 text-purple-200 rounded flex items-center space-x-1 transition-all"
                                      title="Select Parent Element Node"
                                    >
                                      <i className="fa-solid fa-arrow-up text-[10px]"></i>
                                      <span>Select Parent</span>
                                    </button>

                                    <button
                                      type="button"
                                      onClick={handleDeleteInspectedElement}
                                      className="px-2.5 py-1 text-[11px] font-semibold bg-rose-500/20 hover:bg-rose-500/40 text-rose-300 rounded flex items-center space-x-1 border border-rose-500/30 transition-all"
                                      title="Delete Element from HTML Code"
                                    >
                                      <i className="fa-solid fa-trash-can text-[10px]"></i>
                                      <span>Delete</span>
                                    </button>
                                  </div>
                                </div>

                                {/* Quick Edit Inputs Grid */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                                  {/* Text Content Input */}
                                  <div className="space-y-1">
                                    <label className="text-[11px] font-medium text-gray-400">Text Content:</label>
                                    <input
                                      type="text"
                                      value={inspectedElement.innerText || ''}
                                      onChange={(e) => handleUpdateInspectedElement('innerText', e.target.value)}
                                      placeholder="Type inner text..."
                                      className="w-full px-2.5 py-1.5 bg-black/60 border border-white/15 rounded-lg text-gray-200 font-mono text-xs focus:border-purple-500 focus:outline-none"
                                    />
                                  </div>

                                  {/* CSS Classes Input */}
                                  <div className="space-y-1">
                                    <label className="text-[11px] font-medium text-gray-400">CSS Classes:</label>
                                    <input
                                      type="text"
                                      value={inspectedElement.className || ''}
                                      onChange={(e) => handleUpdateInspectedElement('className', e.target.value)}
                                      placeholder="e.g. specsRow specsHd..."
                                      className="w-full px-2.5 py-1.5 bg-black/60 border border-white/15 rounded-lg text-gray-200 font-mono text-xs focus:border-purple-500 focus:outline-none"
                                    />
                                  </div>
                                </div>

                                {/* Element Outer HTML Snippet Editor */}
                                <div className="space-y-1">
                                  <div className="flex justify-between items-center">
                                    <label className="text-[11px] font-medium text-purple-300 flex items-center space-x-1">
                                      <i className="fa-solid fa-code text-[10px]"></i>
                                      <span>Element Outer HTML Code Snippet:</span>
                                    </label>
                                    
                                    {/* Insert Placeholder Dropdown */}
                                    <select
                                      onChange={(e) => {
                                        if (!e.target.value) return;
                                        const tag = e.target.value;
                                        const updated = (inspectedElement.innerText || '') + tag;
                                        handleUpdateInspectedElement('innerText', updated);
                                        e.target.value = '';
                                      }}
                                      className="bg-black/70 border border-purple-500/40 text-xs text-indigo-300 rounded px-2 py-0.5 focus:outline-none"
                                    >
                                      <option value="">+ Insert Placeholder Variable...</option>
                                      {placeholders.map(p => (
                                        <option key={p.name} value={`{${p.name}}`}>{`{${p.name}}`}</option>
                                      ))}
                                    </select>
                                  </div>

                                  <textarea
                                    rows={3}
                                    value={inspectedElement.outerHTML || ''}
                                    onChange={(e) => handleUpdateInspectedElement('outerHTML', e.target.value)}
                                    className="w-full px-2.5 py-1.5 bg-black/80 border border-purple-500/40 rounded-lg text-purple-200 font-mono text-xs focus:border-purple-400 focus:outline-none resize-y"
                                    placeholder="<div class='example'>Content</div>"
                                  ></textarea>
                                </div>
                              </>
                            ) : (
                              <div className="py-3 text-center text-xs text-purple-300/80 flex items-center justify-between px-2">
                                <div className="flex items-center space-x-2">
                                  <i className="fa-solid fa-hand-pointer text-purple-400 animate-bounce"></i>
                                  <span>Hover and click any element in the Live Preview above to Inspect & Edit its HTML code.</span>
                                </div>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setIsVisualEditing(false);
                                    setInspectedElement(null);
                                  }}
                                  className="px-2.5 py-1 text-[11px] font-semibold bg-purple-500/20 hover:bg-purple-500/40 text-purple-200 rounded flex items-center space-x-1 border border-purple-500/30 transition-all shrink-0 ml-2"
                                  title="Turn Off Visual Inspector Mode"
                                >
                                  <i className="fa-solid fa-eye-slash text-[10px]"></i>
                                  <span>Visual OFF</span>
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* FULL SCREEN PREVIEW MODAL */}
                  {showPreviewModal && (
                    <div className="fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex flex-col p-6 animate-fade-in">
                      <div className="flex justify-between items-center mb-4 pb-3 border-b border-white/10">
                        <div className="flex items-center space-x-4">
                          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
                            <i className="fa-solid fa-eye text-white text-sm"></i>
                          </div>
                          <div>
                            <h3 className="font-bold text-white text-base">Full Live Listing Preview</h3>
                            <p className="text-xs text-gray-400">{selectedHtmlCompany} &mdash; {selectedHtmlCategory} / {selectedHtmlSubcategory}</p>
                          </div>

                          {/* Desktop vs Mobile View Mode Segmented Control */}
                          <div className="flex items-center space-x-1 p-0.5 rounded-lg bg-black/40 border border-white/10 ml-4">
                            <button
                              type="button"
                              onClick={() => setPreviewDeviceMode('desktop')}
                              className={`px-3 py-1 text-xs font-semibold rounded flex items-center space-x-1 transition-all ${
                                previewDeviceMode === 'desktop'
                                  ? 'bg-indigo-600 text-white shadow-sm'
                                  : 'text-gray-400 hover:text-white'
                              }`}
                              title="Desktop Full-Width View"
                            >
                              <i className="fa-solid fa-desktop text-[11px]"></i>
                              <span>Desktop</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => setPreviewDeviceMode('mobile')}
                              className={`px-3 py-1 text-xs font-semibold rounded flex items-center space-x-1 transition-all ${
                                previewDeviceMode === 'mobile'
                                  ? 'bg-indigo-600 text-white shadow-sm'
                                  : 'text-gray-400 hover:text-white'
                              }`}
                              title="Mobile Responsive Viewport (380px)"
                            >
                              <i className="fa-solid fa-mobile-screen-button text-[11px]"></i>
                              <span>Mobile</span>
                            </button>
                          </div>

                          {/* Mode Toggle in Modal */}
                          <div className="flex items-center space-x-1 p-0.5 rounded-lg bg-black/40 border border-white/10">
                            <button
                              onClick={() => setPreviewDataMode('raw')}
                              className={`px-3 py-1 text-xs font-semibold rounded transition-all ${
                                previewDataMode === 'raw'
                                  ? 'bg-indigo-600 text-white'
                                  : 'text-gray-400 hover:text-white'
                              }`}
                            >
                              Raw Placeholders
                            </button>
                            <button
                              onClick={() => setPreviewDataMode('sample')}
                              className={`px-3 py-1 text-xs font-semibold rounded transition-all ${
                                previewDataMode === 'sample'
                                  ? 'bg-indigo-600 text-white'
                                  : 'text-gray-400 hover:text-white'
                              }`}
                            >
                              Sample Data
                            </button>
                          </div>

                          <button
                            type="button"
                            onClick={handleOpenDetachedWindow}
                            className={`px-3 py-1.5 text-xs font-bold rounded-lg border transition-all flex items-center space-x-1.5 shadow-md ${
                              isPreviewDetached
                                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30'
                                : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white border-purple-500/30'
                            }`}
                            title="Detach live preview into a separate resizable window"
                          >
                            <i className="fa-solid fa-up-right-from-square text-[10px]"></i>
                            <span>{isPreviewDetached ? 'Refocus Pop-out Window' : '↗ Pop-out Window'}</span>
                          </button>
                        </div>

                        <button
                          onClick={() => setShowPreviewModal(false)}
                          className="px-4 py-2 text-xs font-semibold rounded-xl bg-white/10 hover:bg-rose-600/80 text-white transition-all flex items-center space-x-2"
                        >
                          <i className="fa-solid fa-xmark text-sm"></i>
                          <span>Close Preview</span>
                        </button>
                      </div>

                      <div className={`flex-1 flex justify-center items-center rounded-xl border border-white/20 transition-all ${
                        previewDeviceMode === 'mobile'
                          ? 'bg-slate-950/90 p-6 overflow-y-auto'
                          : 'bg-white overflow-hidden shadow-2xl'
                      }`}>
                        <div className={`transition-all duration-300 ${
                          previewDeviceMode === 'mobile'
                            ? 'w-[380px] h-[680px] border-[10px] border-slate-800 rounded-[36px] shadow-2xl overflow-hidden bg-white relative ring-1 ring-white/20 flex flex-col'
                            : 'w-full h-full'
                        }`}>
                          {previewDeviceMode === 'mobile' && (
                            <div className="w-full bg-slate-800 text-slate-300 py-1.5 px-3 text-[11px] font-mono font-bold border-b border-slate-700 flex justify-between items-center select-none">
                              <span className="flex items-center space-x-1.5 text-indigo-300">
                                <i className="fa-solid fa-mobile-screen-button text-[10px]"></i>
                                <span>Mobile Viewport (380px)</span>
                              </span>
                              <span className="text-[10px] text-slate-400">Preview</span>
                            </div>
                          )}
                          <iframe
                            title="Full Window Live Preview"
                            srcDoc={renderLivePreviewHtml(currentHtmlText, previewDataMode, isVisualEditing)}
                            className="w-full h-full border-0 flex-1"
                            sandbox="allow-scripts allow-same-origin"
                          ></iframe>
                        </div>
                      </div>
                    </div>
                  )}
                    </React.Fragment>
                  )}
                </div>
              )}

              {/* Sub-tab 4: Categories, Setting Columns & Subcategories Manager */}
              {activeTab === 'database' && dbSubTab === 'categories' && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {/* Categories Card */}
                  <div className="glass-card p-4 space-y-3">
                    <div className="flex justify-between items-center">
                      <h3 className="font-bold text-white text-xs flex items-center space-x-1.5">
                        <i className="fa-solid fa-list text-indigo-400"></i>
                        <span>Categories ({dbCategories.length})</span>
                      </h3>
                      <button
                        onClick={() => setShowAddCatModal(true)}
                        className="btn-primary px-2 py-1 text-[11px] flex items-center space-x-1"
                      >
                        <i className="fa-solid fa-plus text-[9px]"></i>
                        <span>+ Add</span>
                      </button>
                    </div>

                    <div className="space-y-1.5 max-h-80 overflow-y-auto pr-1">
                      {dbCategories.map(c => (
                        <div key={c.id} className="p-2.5 glass-card bg-white/[0.02] flex justify-between items-center text-xs">
                          <span className="font-medium text-gray-200 truncate">{c.name}</span>
                          <div className="flex items-center space-x-1">
                            <button
                              onClick={() => handleEditCategoryInDb(c)}
                              className="text-indigo-400 hover:text-indigo-300 p-1"
                              title="Rename category"
                            >
                              <i className="fa-solid fa-pen text-[10px]"></i>
                            </button>
                            {isAdminMode && c.name.toLowerCase() !== 'default' && (
                              <button
                                onClick={() => handleDeleteCategoryFromDb(c.id)}
                                className="text-rose-400 hover:text-rose-300 p-1"
                                title="Delete category from DB"
                              >
                                <i className="fa-solid fa-trash text-[10px]"></i>
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Subcategories Card */}
                  <div className="glass-card p-4 space-y-3">
                    <div className="flex justify-between items-center">
                      <h3 className="font-bold text-white text-xs flex items-center space-x-1.5">
                        <i className="fa-solid fa-tags text-emerald-400"></i>
                        <span>Subcategories ({dbSubcategories.length})</span>
                      </h3>
                      <button
                        onClick={() => setShowAddSubcatModal(true)}
                        className="btn-primary px-2 py-1 text-[11px] flex items-center space-x-1"
                      >
                        <i className="fa-solid fa-plus text-[9px]"></i>
                        <span>+ Add</span>
                      </button>
                    </div>

                    <div className="space-y-1.5 max-h-80 overflow-y-auto pr-1">
                      {dbSubcategories.map(sub => (
                        <div key={sub.id} className="p-2.5 glass-card bg-white/[0.02] flex justify-between items-center text-xs">
                          <div className="flex items-center space-x-1.5 truncate">
                            <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                              {sub.category || 'Engagement Ring'}
                            </span>
                            <span className="font-medium text-gray-200 truncate">{sub.name}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            {sub.name.toLowerCase() !== 'default' && (
                              <button
                                onClick={() => handleEditSubcategoryInDb(sub)}
                                className="text-indigo-400 hover:text-indigo-300 p-1"
                                title="Rename subcategory"
                              >
                                <i className="fa-solid fa-pen text-[10px]"></i>
                              </button>
                            )}
                            {isAdminMode && sub.name.toLowerCase() !== 'default' && (
                              <button
                                onClick={() => handleDeleteSubcategoryFromDb(sub.id)}
                                className="text-rose-400 hover:text-rose-300 p-1"
                                title="Delete subcategory from DB"
                              >
                                <i className="fa-solid fa-trash text-[10px]"></i>
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Setting Columns Card */}
                  <div className="glass-card p-4 space-y-3">
                    <div className="flex justify-between items-center">
                      <h3 className="font-bold text-white text-xs flex items-center space-x-1.5">
                        <i className="fa-solid fa-table-columns text-purple-400"></i>
                        <span>Setting Columns ({dbSettingColumns.length})</span>
                      </h3>
                      <button
                        onClick={() => setShowAddColModal(true)}
                        className="btn-primary px-2 py-1 text-[11px] flex items-center space-x-1"
                      >
                        <i className="fa-solid fa-plus text-[9px]"></i>
                        <span>+ Add</span>
                      </button>
                    </div>

                    <div className="space-y-1.5 max-h-80 overflow-y-auto pr-1">
                      {dbSettingColumns.map(col => (
                        <div key={col.id} className="p-2.5 glass-card bg-white/[0.02] flex justify-between items-center text-xs">
                          <span className="font-medium text-gray-200 truncate">{col.name}</span>
                          <div className="flex items-center space-x-1">
                            {col.name.toLowerCase() !== 'default' && (
                              <button
                                onClick={() => handleEditSettingColumnInDb(col)}
                                className="text-indigo-400 hover:text-indigo-300 p-1"
                                title="Rename setting column"
                              >
                                <i className="fa-solid fa-pen text-[10px]"></i>
                              </button>
                            )}
                            {isAdminMode && col.name.toLowerCase() !== 'default' && (
                              <button
                                onClick={() => handleDeleteSettingColumnFromDb(col.id)}
                                className="text-rose-400 hover:text-rose-300 p-1"
                                title="Delete setting column from DB"
                              >
                                <i className="fa-solid fa-trash text-[10px]"></i>
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Product Sheets Card */}
                  <div className="glass-card p-4 space-y-3">
                    <div className="flex justify-between items-center">
                      <h3 className="font-bold text-white text-xs flex items-center space-x-1.5">
                        <i className="fa-solid fa-box-open text-amber-400"></i>
                        <span>Product Sheets ({products.length})</span>
                      </h3>
                      <button
                        onClick={() => {
                          setEditModalConfig({
                            title: 'Add New Product Sheet',
                            label: 'Product Sheet Name:',
                            initialValue: '',
                            placeholder: 'e.g. BRACELET, EARRINGS, RING, NECKLACE',
                            onSave: async (pName) => {
                              if (!pName || !pName.trim()) return;
                              await callEel('save_product', pName.trim());
                              showToast(`Product sheet "${pName.trim()}" added!`, 'success');
                              await reloadCompaniesAndProducts();
                            }
                          });
                        }}
                        className="btn-primary px-2 py-1 text-[11px] flex items-center space-x-1"
                      >
                        <i className="fa-solid fa-plus text-[9px]"></i>
                        <span>+ Add</span>
                      </button>
                    </div>

                    <div className="space-y-1.5 max-h-80 overflow-y-auto pr-1">
                      {products.map((p, idx) => (
                        <div key={idx} className="p-2.5 glass-card bg-white/[0.02] flex justify-between items-center text-xs">
                          <span className="font-medium text-gray-200 truncate">{p}</span>
                          {isAdminMode && (
                            <button
                              onClick={async () => {
                                await callEel('delete_product', p);
                                showToast(`Product sheet "${p}" deleted!`, 'success');
                                await reloadCompaniesAndProducts();
                              }}
                              className="text-rose-400 hover:text-rose-300 p-1"
                              title="Delete product sheet"
                            >
                              <i className="fa-solid fa-trash text-[10px]"></i>
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Sub-tab 5: Database Safety, Backup & Restore */}
              {activeTab === 'database' && dbSubTab === 'backup' && (
                <div className="space-y-6">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-card p-6 border border-indigo-500/40 rounded-2xl shadow-xl">
                    <div className="space-y-1">
                      <h3 className="text-xl font-bold text-indigo-300 flex items-center space-x-3">
                        <i className="fa-solid fa-database text-purple-400"></i>
                        <span>Full SQLite Database Backup & Restore Manager (All Masters)</span>
                      </h3>
                      <p className="text-xs text-gray-300">
                        Create a complete, 100% full snapshot of <code className="bg-black/50 px-1.5 py-0.5 rounded text-amber-300">app_database.db</code> including all master tables (Categories, Subcategories, Setting Columns, Title Formulas, HTML Layouts, Company Policies, Products, Placeholders & Mappings).
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                      <button
                        onClick={() => {
                          setBackupDescriptionInput('');
                          setShowBackupCreateModal(true);
                        }}
                        disabled={isDbOperationPending}
                        className="px-4 py-2.5 text-xs font-bold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 rounded-xl shadow-lg shadow-emerald-500/20 flex items-center space-x-2 transition-all disabled:opacity-50 cursor-pointer"
                      >
                        <i className="fa-solid fa-download text-sm"></i>
                        <span>Create Instant Backup</span>
                      </button>

                      <label className="px-4 py-2.5 text-xs font-bold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 rounded-xl shadow-lg shadow-indigo-500/20 flex items-center space-x-2 transition-all cursor-pointer">
                        <i className="fa-solid fa-upload text-sm"></i>
                        <span>Restore DB File</span>
                        <input
                          type="file"
                          accept=".db,.sqlite"
                          className="hidden"
                          onChange={handleRestoreFromFileUpload}
                        />
                      </label>
                    </div>
                  </div>

                  {/* Backups History Table Card */}
                  <div className="glass-card p-6 space-y-4 rounded-2xl border border-white/10">
                    <div className="flex justify-between items-center border-b border-white/10 pb-4">
                      <h4 className="font-semibold text-sm text-gray-200 flex items-center space-x-2">
                        <i className="fa-solid fa-clock-rotate-left text-amber-400 text-base"></i>
                        <span>Available Database Backups ({dbBackupsList.length})</span>
                      </h4>
                      <button
                        onClick={fetchBackupsList}
                        className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
                      >
                        <i className="fa-solid fa-rotate text-xs"></i>
                        <span>Refresh List</span>
                      </button>
                    </div>

                    {dbBackupsList.length === 0 ? (
                      <div className="text-center py-12 space-y-3">
                        <i className="fa-solid fa-folder-open text-4xl text-gray-600"></i>
                        <p className="text-xs text-gray-400">
                          No database backups found in <code className="bg-black/50 px-2 py-0.5 rounded text-amber-300">backups/</code> directory yet.
                        </p>
                        <button
                          onClick={() => {
                            setBackupDescriptionInput('');
                            setShowBackupCreateModal(true);
                          }}
                          className="px-3 py-1.5 bg-indigo-600/40 text-indigo-300 border border-indigo-500/40 rounded-lg text-xs font-semibold hover:bg-indigo-600/60"
                        >
                          Create First Backup Now
                        </button>
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs text-left text-gray-300">
                          <thead className="bg-white/5 text-gray-400 uppercase font-mono border-b border-white/10">
                            <tr>
                              <th className="p-3">Backup File</th>
                              <th className="p-3">Description / Note</th>
                              <th className="p-3">Date Created</th>
                              <th className="p-3">File Size</th>
                              <th className="p-3 text-right">Actions</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-white/5">
                            {dbBackupsList.map((b, idx) => (
                              <tr key={idx} className="hover:bg-white/5 transition-colors">
                                <td className="p-3 font-mono text-indigo-300 font-semibold flex items-center space-x-2">
                                  <i className="fa-solid fa-file-database text-purple-400"></i>
                                  <span>{b.filename}</span>
                                </td>
                                <td className="p-3">
                                  {b.description ? (
                                    <span className="text-emerald-300 font-sans italic bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/30 inline-block max-w-[280px] truncate" title={b.description}>
                                      🏷️ {b.description}
                                    </span>
                                  ) : (
                                    <button
                                      onClick={() => handleEditBackupNote(b)}
                                      className="text-gray-500 hover:text-indigo-300 italic text-[11px] flex items-center space-x-1"
                                      title="Add description note"
                                    >
                                      <i className="fa-solid fa-plus text-[9px]"></i>
                                      <span>Add description note...</span>
                                    </button>
                                  )}
                                </td>
                                <td className="p-3 text-gray-400">{b.created_at}</td>
                                <td className="p-3 text-gray-400 font-mono">{(b.size_bytes / 1024).toFixed(1)} KB</td>
                                <td className="p-3 text-right space-x-1.5">
                                  <button
                                    onClick={() => handleEditBackupNote(b)}
                                    className="px-2.5 py-1 bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/40 rounded-lg font-semibold text-xs transition-colors inline-flex items-center space-x-1"
                                    title="Edit description note for this backup"
                                  >
                                    <i className="fa-solid fa-pen text-[10px]"></i>
                                    <span>Note</span>
                                  </button>
                                  <button
                                    onClick={() => handleRestoreFromPath(b.path)}
                                    className="px-2.5 py-1 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 rounded-lg font-semibold text-xs transition-colors inline-flex items-center space-x-1"
                                    title="Restore database from this backup file"
                                  >
                                    <i className="fa-solid fa-rotate-left text-[11px]"></i>
                                    <span>Restore</span>
                                  </button>
                                  {isAdminMode && (
                                    <button
                                      onClick={() => handleDeleteBackupFile(b.filename)}
                                      className="px-2 py-1 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 rounded-lg font-semibold text-xs transition-colors inline-flex items-center space-x-1"
                                      title="Delete backup file (Admin Mode Only)"
                                    >
                                      <i className="fa-solid fa-trash text-[10px]"></i>
                                    </button>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'mapping' && (
            <div className="w-full h-full flex flex-col flex-1 min-h-0 space-y-4">
              {/* Mapping Rules List Grid */}
              {(() => {
                const filtered = excelMappings.filter(m => {
                  const mSrc = (m.source_sheet || '').trim();
                  const mTgt = (m.target_sheet || '').trim();

                  let matchSource = false;
                  if (mappingFilterSource === 'all') {
                    matchSource = true;
                  } else if (mappingFilterSource === '[ALL]') {
                    matchSource = mSrc === '[ALL]' || mSrc.toLowerCase() === 'all';
                  } else {
                    matchSource = mSrc === mappingFilterSource || mSrc === '[ALL]' || mSrc.toLowerCase() === 'all';
                  }

                  let matchTarget = false;
                  if (mappingFilterTarget === 'all') {
                    matchTarget = true;
                  } else if (mappingFilterTarget === '[ALL]') {
                    matchTarget = mTgt === '[ALL]' || mTgt.toLowerCase() === 'all';
                  } else {
                    matchTarget = mTgt === mappingFilterTarget || mTgt === '[ALL]' || mTgt.toLowerCase() === 'all';
                  }

                  let matchComp = false;
                  const mComp = (m.company_name || 'All').trim();
                  if (mappingFilterCompany === 'all') {
                    matchComp = true;
                  } else if (mappingFilterCompany === 'All') {
                    matchComp = mComp.toLowerCase() === 'all';
                  } else {
                    matchComp = mComp.toLowerCase() === mappingFilterCompany.toLowerCase() || mComp.toLowerCase() === 'all';
                  }

                  let matchCol = false;
                  const mCol = (m.target_column || '').trim();
                  if (mappingFilterColumn === 'all') {
                    matchCol = true;
                  } else {
                    matchCol = mCol.toLowerCase() === mappingFilterColumn.toLowerCase();
                  }

                  if (!matchSource || !matchTarget || !matchComp || !matchCol) return false;

                  if (mappingSearch.trim()) {
                    const q = mappingSearch.toLowerCase().trim();
                    return (m.source_column || '').toLowerCase().includes(q) || 
                           (m.target_column || '').toLowerCase().includes(q) || 
                           (m.company_name || '').toLowerCase().includes(q) ||
                           (m.default_value || '').toLowerCase().includes(q) ||
                           (m.mapping_type || '').toLowerCase().includes(q) ||
                           mSrc.toLowerCase().includes(q) || 
                           mTgt.toLowerCase().includes(q);
                  }
                  return true;
                });

                filtered.sort((a, b) => {
                  if (mappingSortBy === 'alpha_target_col') {
                    const colA = (a.target_column || '').trim().toLowerCase();
                    const colB = (b.target_column || '').trim().toLowerCase();
                    if (colA !== colB) return colA.localeCompare(colB);

                    const sheetA = (a.target_sheet || '').trim().toLowerCase();
                    const sheetB = (b.target_sheet || '').trim().toLowerCase();
                    if (sheetA !== sheetB) return sheetA.localeCompare(sheetB);

                    const srcA = (a.source_sheet || '').trim().toLowerCase();
                    const srcB = (b.source_sheet || '').trim().toLowerCase();
                    if (srcA !== srcB) return srcA.localeCompare(srcB);

                    return (a.id || 0) - (b.id || 0);
                  }

                  if (mappingSortBy === 'alpha_target_sheet') {
                    const sheetA = (a.target_sheet || '').trim().toLowerCase();
                    const sheetB = (b.target_sheet || '').trim().toLowerCase();
                    if (sheetA !== sheetB) return sheetA.localeCompare(sheetB);

                    const colA = (a.target_column || '').trim().toLowerCase();
                    const colB = (b.target_column || '').trim().toLowerCase();
                    if (colA !== colB) return colA.localeCompare(colB);

                    return (a.id || 0) - (b.id || 0);
                  }

                  if (mappingSortBy === 'alpha_source_sheet') {
                    const srcA = (a.source_sheet || '').trim().toLowerCase();
                    const srcB = (b.source_sheet || '').trim().toLowerCase();
                    if (srcA !== srcB) return srcA.localeCompare(srcB);

                    const sheetA = (a.target_sheet || '').trim().toLowerCase();
                    const sheetB = (b.target_sheet || '').trim().toLowerCase();
                    if (sheetA !== sheetB) return sheetA.localeCompare(sheetB);

                    const colA = (a.target_column || '').trim().toLowerCase();
                    const colB = (b.target_column || '').trim().toLowerCase();
                    return colA.localeCompare(colB);
                  }

                  if (mappingSortBy === 'alpha_company') {
                    const compA = (a.company_name || 'All').trim().toLowerCase();
                    const compB = (b.company_name || 'All').trim().toLowerCase();
                    if (compA !== compB) return compA.localeCompare(compB);

                    const colA = (a.target_column || '').trim().toLowerCase();
                    const colB = (b.target_column || '').trim().toLowerCase();
                    if (colA !== colB) return colA.localeCompare(colB);

                    const sheetA = (a.target_sheet || '').trim().toLowerCase();
                    const sheetB = (b.target_sheet || '').trim().toLowerCase();
                    return sheetA.localeCompare(sheetB);
                  }

                  // Default 'id_asc': Group by column name & sheet name for clean display
                  const colA = (a.target_column || '').trim().toLowerCase();
                  const colB = (b.target_column || '').trim().toLowerCase();
                  if (colA !== colB) return colA.localeCompare(colB);

                  const sheetA = (a.target_sheet || '').trim().toLowerCase();
                  const sheetB = (b.target_sheet || '').trim().toLowerCase();
                  if (sheetA !== sheetB) return sheetA.localeCompare(sheetB);

                  return (a.id || 0) - (b.id || 0);
                });

                if (filtered.length === 0) {
                  return (
                    <div className="glass-card p-12 text-center space-y-3">
                      <i className="fa-solid fa-diagram-project text-4xl text-gray-600"></i>
                      <div className="text-gray-300 font-semibold">No Excel Mapping Rules Found</div>
                      <p className="text-gray-500 text-xs max-w-sm mx-auto">
                        No mappings match your selected filters. Click "Add Column Mapping" or "Reset Defaults" to create mapping rules.
                      </p>
                    </div>
                  );
                }

                return (
                  <div className="glass-card flex-1 min-h-0 flex flex-col overflow-hidden shadow-2xl">
                    <div className="overflow-auto flex-1 min-h-0 custom-scrollbar">
                      <table className="w-full text-left text-xs">
                        <thead className="sticky top-0 z-10 bg-indigo-950/95 backdrop-blur-md text-gray-200 uppercase font-bold tracking-wider text-[11px] border-b border-indigo-500/40 shadow-md">
                          <tr>
                            <th className="py-3.5 pl-6 pr-4 min-w-[120px]">Company</th>
                            <th className="py-3.5 px-4 min-w-[220px]">Source Excel Sheet & Column</th>
                            <th className="py-3.5 px-3 text-center w-24">Map Direction</th>
                            <th className="py-3.5 px-4 min-w-[240px]">Target Multi_API Sheet & Column</th>
                            <th className="py-3.5 px-4 min-w-[110px]">Mapping Type</th>
                            <th className="py-3.5 px-4 min-w-[130px]">Default Value</th>
                            <th className="py-3.5 pl-4 pr-6 text-right w-24">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                          {filtered.map(m => (
                            <tr 
                              key={m.id} 
                              onClick={() => {
                                if (isAdminMode) {
                                  setSelectedMappingAction(m);
                                } else {
                                  const { id, ...copyData } = m;
                                  setEditingMapping({ ...copyData, id: null });
                                  setShowMappingModal(true);
                                }
                              }}
                              className="transition-colors cursor-pointer hover:bg-indigo-500/15" 
                            >
                              <td className="py-3.5 pl-6 pr-4">
                                <span className={`px-2.5 py-1 rounded font-mono text-[11px] font-bold border inline-block ${
                                  (!m.company_name || m.company_name.toLowerCase() === 'all')
                                    ? 'bg-slate-500/20 text-slate-300 border-slate-500/30'
                                    : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                                }`}>
                                  {m.company_name || 'All'}
                                </span>
                              </td>
                              <td className="py-3.5 px-4">
                                <div className="flex items-center space-x-2">
                                  <span className={`px-2 py-0.5 rounded font-mono text-[11px] font-bold border ${
                                    m.source_sheet === '[ALL]' ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' : 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30'
                                  }`}>
                                    {m.source_sheet}
                                  </span>
                                  <span className="font-semibold text-white">{m.source_column}</span>
                                </div>
                              </td>
                              <td className="py-3.5 px-3 text-center text-indigo-400 font-bold">
                                <i className="fa-solid fa-arrow-right"></i>
                              </td>
                              <td className="py-3.5 px-4">
                                <div className="flex items-center space-x-2">
                                  <span className={`px-2 py-0.5 rounded font-mono text-[11px] font-bold border ${
                                    m.target_sheet === '[ALL]' ? 'bg-emerald-500/30 text-emerald-200 border-emerald-400/50 shadow-sm' : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                                  }`}>
                                    {m.target_sheet}
                                  </span>
                                  <span className="font-semibold text-white">{m.target_column}</span>
                                </div>
                              </td>
                              <td className="py-3.5 px-4">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                                  m.mapping_type === 'direct' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' :
                                  m.mapping_type === 'template' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' :
                                  'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                }`}>
                                  {m.mapping_type || 'direct'}
                                </span>
                              </td>
                              <td className="py-3.5 px-4 text-gray-400 italic font-mono text-xs">
                                {m.default_value ? m.default_value : <span className="text-gray-600">None</span>}
                              </td>
                              <td className="py-3.5 pl-4 pr-6 text-right">
                                <div className="flex items-center justify-end space-x-2">
                                  {isAdminMode && (
                                    <button
                                      type="button"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setEditingMapping({ ...m });
                                        setShowMappingModal(true);
                                      }}
                                      className="p-1.5 text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/20 rounded-lg transition-colors"
                                      title="Edit mapping rule"
                                    >
                                      <i className="fa-solid fa-pen-to-square"></i>
                                    </button>
                                  )}
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      const { id, ...copyData } = m;
                                      setEditingMapping({ ...copyData, id: null });
                                      setShowMappingModal(true);
                                    }}
                                    className="p-1.5 text-amber-400 hover:text-amber-300 hover:bg-amber-500/20 rounded-lg transition-colors"
                                    title="Copy/Duplicate mapping rule"
                                  >
                                    <i className="fa-solid fa-copy"></i>
                                  </button>
                                  {isAdminMode && (
                                    <button
                                      type="button"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleDeleteMapping(m.id);
                                      }}
                                      className="p-1.5 text-rose-400 hover:text-rose-300 hover:bg-rose-500/20 rounded-lg transition-colors"
                                      title="Delete mapping rule"
                                    >
                                      <i className="fa-solid fa-trash"></i>
                                    </button>
                                  )}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                );
              })()}
            </div>
          )}

          {activeTab === 'settings' && (

            <div className="max-w-3xl mx-auto space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center space-x-3">
                  <i className="fa-solid fa-circle-info text-amber-400"></i>
                  <span>System & Environment Information</span>
                </h2>
                <p className="text-gray-400 text-sm mt-1">
                  Overview of SQLite Database status, API export settings, and navigation sidebar customization.
                </p>
              </div>

              {/* Custom Navigation Sidebar Renamer Card */}
              <div className="p-6 glass-card bg-indigo-950/20 border-indigo-500/30 space-y-4">
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                  <div>
                    <h3 className="text-base font-bold text-white flex items-center space-x-2">
                      <i className="fa-solid fa-pen-to-square text-indigo-400"></i>
                      <span>Customize Navigation Sidebar Titles</span>
                    </h3>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Rename any navigation item in the left sidebar (e.g. change "Database Manager Master" to "Data Master").
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      onClick={handleSaveNavLabels}
                      className="px-4 py-1.5 text-xs font-bold rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-md border border-indigo-400/40 transition-all flex items-center space-x-1.5 cursor-pointer hover:scale-105"
                      title="Save customized navigation sidebar titles to LocalStorage"
                    >
                      <i className="fa-solid fa-floppy-disk text-xs"></i>
                      <span>Save Changes</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleResetNavLabels}
                      className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 transition-all flex items-center space-x-1.5"
                      title="Reset all sidebar navigation titles to default"
                    >
                      <i className="fa-solid fa-rotate-left text-[11px]"></i>
                      <span>Reset Defaults</span>
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-300 mb-1">
                      1. Data Generator Tab Name:
                    </label>
                    <input
                      type="text"
                      value={navLabels.generator || ''}
                      onChange={(e) => handleUpdateNavLabel('generator', e.target.value)}
                      placeholder="e.g. Data Generator Master"
                      className="w-full glass-input px-3 py-2 text-xs font-bold text-indigo-200"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-300 mb-1">
                      2. HTML App / Modifier Tab Name:
                    </label>
                    <input
                      type="text"
                      value={navLabels.html_master || ''}
                      onChange={(e) => handleUpdateNavLabel('html_master', e.target.value)}
                      placeholder="e.g. HTML App (Modifier) Master"
                      className="w-full glass-input px-3 py-2 text-xs font-bold text-purple-200"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-300 mb-1">
                      3. Database Manager Tab Name:
                    </label>
                    <input
                      type="text"
                      value={navLabels.database || ''}
                      onChange={(e) => handleUpdateNavLabel('database', e.target.value)}
                      placeholder="e.g. Data Master or Database Manager Master"
                      className="w-full glass-input px-3 py-2 text-xs font-bold text-emerald-200"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-300 mb-1">
                      4. Excel Mapping Tab Name:
                    </label>
                    <input
                      type="text"
                      value={navLabels.mapping || ''}
                      onChange={(e) => handleUpdateNavLabel('mapping', e.target.value)}
                      placeholder="e.g. Excel Mapping Master"
                      className="w-full glass-input px-3 py-2 text-xs font-bold text-amber-200"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-xs font-semibold text-gray-300 mb-1">
                      5. System Info / Settings Tab Name:
                    </label>
                    <input
                      type="text"
                      value={navLabels.settings || ''}
                      onChange={(e) => handleUpdateNavLabel('settings', e.target.value)}
                      placeholder="e.g. System Info Master"
                      className="w-full glass-input px-3 py-2 text-xs font-bold text-blue-200"
                    />
                  </div>
                </div>

                {/* Footer Save & Reset Action Bar */}
                <div className="flex justify-end items-center pt-3 border-t border-white/10 space-x-3">
                  <button
                    type="button"
                    onClick={handleResetNavLabels}
                    className="px-3.5 py-1.5 text-xs font-semibold rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 transition-all flex items-center space-x-1.5"
                  >
                    <i className="fa-solid fa-rotate-left text-xs"></i>
                    <span>Reset Defaults</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleSaveNavLabels}
                    className="px-5 py-2 text-xs font-bold rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-lg border border-indigo-400/40 transition-all flex items-center space-x-2 hover:scale-105"
                  >
                    <i className="fa-solid fa-floppy-disk text-xs"></i>
                    <span>Save Changes</span>
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-5 glass-card space-y-2 border-indigo-500/30">
                  <div className="text-xs text-gray-400 uppercase font-semibold">Primary Database</div>
                  <div className="text-sm font-bold text-indigo-300">app_database.db (SQLite3)</div>
                  <p className="text-xs text-gray-400">Replaced legacy Excel & hardcoded python templates with high-speed SQLite storage.</p>
                </div>

                <div className="p-5 glass-card space-y-2 border-emerald-500/30">
                  <div className="text-xs text-gray-400 uppercase font-semibold">API Target Export</div>
                  <div className="text-sm font-bold text-emerald-300">Multi_API.xlsx</div>
                  <p className="text-xs text-gray-400">Master output template for generating listing API rows.</p>
                </div>
              </div>
            </div>
          )}
        </main>

      {/* Selected Mapping Row Action Popup Modal */}
      {selectedMappingAction && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-fadeIn">
          <div className="glass-card max-w-md w-full p-6 space-y-5 border-indigo-500/40 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <i className="fa-solid fa-sliders text-indigo-400"></i>
                <span>Manage Column Mapping Rule</span>
              </h3>
              <button
                type="button"
                onClick={() => setSelectedMappingAction(null)}
                className="text-gray-400 hover:text-white text-sm"
              >
                <i className="fa-solid fa-xmark"></i>
              </button>
            </div>

            {/* Rule Summary */}
            <div className="p-4 glass-card bg-black/40 border-white/10 space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-gray-400 font-semibold">Target Company:</span>
                <span className="font-bold text-amber-300 font-mono px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30">
                  {selectedMappingAction.company_name || 'All'}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-400 font-semibold">Source Sheet & Column:</span>
                <span className="font-bold text-indigo-300 font-mono">
                  {selectedMappingAction.source_sheet} &rarr; {selectedMappingAction.source_column}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-400 font-semibold">Target Sheet & Column:</span>
                <span className="font-bold text-emerald-300 font-mono">
                  {selectedMappingAction.target_sheet} &rarr; {selectedMappingAction.target_column}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-400 font-semibold">Mapping Type:</span>
                <span className="font-bold text-gray-200 uppercase font-mono">
                  {selectedMappingAction.mapping_type}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-400 font-semibold">Default Constant Value:</span>
                <span className="font-bold text-purple-300 font-mono">
                  {selectedMappingAction.default_value || 'None'}
                </span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex space-x-3 pt-1">
              <button
                type="button"
                onClick={() => {
                  setEditingMapping({ ...selectedMappingAction });
                  setSelectedMappingAction(null);
                  setShowMappingModal(true);
                }}
                className="flex-1 btn-primary py-2.5 text-xs font-bold flex items-center justify-center space-x-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 shadow-lg shadow-indigo-600/30"
              >
                <i className="fa-solid fa-pen-to-square"></i>
                <span>Edit Mapping Rule</span>
              </button>

              <button
                type="button"
                onClick={async () => {
                  const ruleId = selectedMappingAction.id;
                  setSelectedMappingAction(null);
                  await handleDeleteMapping(ruleId);
                }}
                className="flex-1 py-2.5 text-xs font-bold flex items-center justify-center space-x-2 bg-rose-500/20 hover:bg-rose-500/40 text-rose-300 border border-rose-500/30 rounded-xl transition-all"
              >
                <i className="fa-solid fa-trash"></i>
                <span>Delete Rule</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Excel Mapping Modal */}
      {showMappingModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <i className="fa-solid fa-table-columns text-indigo-400"></i>
                <span>{editingMapping?.id ? 'Edit Column Mapping' : (editingMapping?.source_column || editingMapping?.target_column) ? 'Copy / Duplicate Column Mapping' : 'Add New Column Mapping'}</span>
              </h3>
              <button
                onClick={() => {
                  setShowMappingModal(false);
                  setEditingMapping(null);
                }}
                className="text-gray-400 hover:text-white text-sm"
              >
                <i className="fa-solid fa-xmark"></i>
              </button>
            </div>

            <form onSubmit={handleSaveMapping} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 font-semibold block mb-1">Target Company Rule *</label>
                <select
                  value={editingMapping?.company_name || 'All'}
                  onChange={(e) => setEditingMapping({ ...editingMapping, company_name: e.target.value })}
                  className="glass-input w-full px-3 py-2 text-xs font-semibold text-amber-300"
                >
                  <option value="All" className="bg-gray-900 text-amber-300 font-bold">✨ All Companies (Global Default Rule)</option>
                  {companies.map(c => (
                    <option key={c} value={c} className="bg-gray-900 text-white">{c}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-400 font-semibold block mb-1">Source Sheet Name *</label>
                  <select
                    value={editingMapping?.source_sheet || (availableInputSheets[0] || 'RING')}
                    onChange={(e) => {
                      const newSrc = e.target.value;
                      const validTargets = getFilteredTargetSheets(newSrc, availableTargetSheets);
                      let newTgt = editingMapping?.target_sheet || '[ALL]';
                      if (newTgt !== '[ALL]' && !validTargets.includes(newTgt)) {
                        newTgt = validTargets[0] || '[ALL]';
                      }
                      setEditingMapping({ ...editingMapping, source_sheet: newSrc, target_sheet: newTgt });
                    }}
                    className="glass-input w-full px-3 py-2 text-xs font-semibold text-indigo-300"
                    required
                  >
                    <option value="[ALL]" className="bg-gray-900 text-amber-300 font-bold">✨ [ALL] (Applies to All Input Sheets)</option>
                    {availableInputSheets.map(s => (
                      <option key={s} value={s} className="bg-gray-900 text-white">{s}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-400 font-semibold block mb-1">
                    Source Column Name {editingMapping?.mapping_type === 'static' ? '(Optional for Static)' : '*'}
                  </label>
                  <input
                    type="text"
                    placeholder={editingMapping?.mapping_type === 'static' ? 'Optional (Defaults to [DEFAULT])' : 'e.g. SKU, Price, Style'}
                    value={editingMapping?.source_column || ''}
                    onChange={(e) => setEditingMapping({ ...editingMapping, source_column: e.target.value })}
                    className="glass-input w-full px-3 py-2 text-xs"
                    required={editingMapping?.mapping_type !== 'static'}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-400 font-semibold block mb-1">Target Sheet Name *</label>
                  <select
                    value={editingMapping?.target_sheet || (availableTargetSheets[0] || 'Cat-EngagementRings')}
                    onChange={(e) => setEditingMapping({ ...editingMapping, target_sheet: e.target.value })}
                    className="glass-input w-full px-3 py-2 text-xs font-semibold text-emerald-300"
                    required
                  >
                    <option value="[ALL]" className="bg-gray-900 text-amber-300 font-bold">✨ [ALL] (Applies to All Target Sheets)</option>
                    {getFilteredTargetSheets(editingMapping?.source_sheet || (availableInputSheets[0] || 'RING'), availableTargetSheets).map(t => (
                      <option key={t} value={t} className="bg-gray-900 text-white">{t}</option>
                    ))}
                  </select>
                </div>


                <div>
                  <label className="text-xs text-gray-400 font-semibold block mb-1">Target Column Name *</label>
                  <input
                    type="text"
                    placeholder="e.g. Custom label (SKU), Condition ID"
                    value={editingMapping?.target_column || ''}
                    onChange={(e) => setEditingMapping({ ...editingMapping, target_column: e.target.value })}
                    className="glass-input w-full px-3 py-2 text-xs"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-400 font-semibold block mb-1">Mapping Type</label>
                  <select
                    value={editingMapping?.mapping_type || 'direct'}
                    onChange={(e) => setEditingMapping({ ...editingMapping, mapping_type: e.target.value })}
                    className="glass-input w-full px-3 py-2 text-xs font-semibold"
                  >
                    <option value="direct">Direct Copy (Input Value)</option>
                    <option value="template">Template / Formula</option>
                    <option value="static">Static Constant Value</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-400 font-semibold block mb-1">
                    {editingMapping?.mapping_type === 'static' ? 'Constant Value *' : 'Default / Fallback Value'}
                  </label>
                  <input
                    ref={defaultValueInputRef}
                    type="text"
                    placeholder={editingMapping?.mapping_type === 'static' ? 'e.g. {GOLD_KT} Solid Gold | Diamond' : 'e.g. {GOLD_KT} {GOLD_COLOR}'}
                    value={editingMapping?.default_value || ''}
                    onChange={(e) => setEditingMapping({ ...editingMapping, default_value: e.target.value })}
                    className="glass-input w-full px-3 py-2 text-xs"
                    required={editingMapping?.mapping_type === 'static'}
                  />
                </div>
              </div>

              {/* Interactive Placeholder Chips toolbar (FULL WIDTH) */}
              <div className="space-y-2 p-3 glass-card bg-black/40 border border-white/10 rounded-xl w-full">
                <div className="flex items-center justify-between text-[11px] text-gray-400 font-semibold">
                  <span className="flex items-center space-x-1.5">
                    <i className="fa-solid fa-code text-indigo-400"></i>
                    <span>Click tag to insert/replace text:</span>
                  </span>
                </div>

                <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto py-1">
                  {customPlaceholders.map(ph => (
                    <span
                      key={ph}
                      onClick={() => handleInsertPlaceholder(ph)}
                      className="inline-flex items-center px-2 py-0.5 rounded-lg text-[11px] font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/40 hover:text-white cursor-pointer transition-all shadow-sm group select-none"
                      title={`Click to replace selected text or insert ${ph}`}
                    >
                      <span>{ph}</span>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemoveCustomPlaceholder(ph);
                        }}
                        className="text-indigo-400/50 hover:text-rose-400 ml-1.5 opacity-0 group-hover:opacity-100 transition-opacity font-sans font-bold"
                        title="Remove tag from quick list"
                      >
                        &times;
                      </button>
                    </span>
                  ))}
                </div>

                {/* Add Custom Tag Form */}
                <div className="flex items-center space-x-2 pt-1 border-t border-white/5">
                  <input
                    type="text"
                    placeholder="Add tag e.g. GOLD_KT"
                    value={newPlaceholderInput}
                    onChange={(e) => setNewPlaceholderInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddCustomPlaceholder(e);
                      }
                    }}
                    className="glass-input text-[11px] px-2.5 py-1 flex-1 rounded-lg"
                  />
                  <button
                    type="button"
                    onClick={handleAddCustomPlaceholder}
                    className="px-3 py-1 glass-button bg-indigo-600/80 hover:bg-indigo-500 text-white text-[11px] font-medium rounded-lg"
                  >
                    + Add Tag
                  </button>
                </div>
              </div>


              <div className="flex justify-end space-x-2 pt-2 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => {
                    setShowMappingModal(false);
                    setEditingMapping(null);
                  }}
                  className="px-4 py-2 glass-button bg-gray-800 text-xs font-medium rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 glass-button bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-xl shadow-lg shadow-indigo-600/25"
                >
                  Save Mapping
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Quick Add Category Modal */}
      {showAddCatModal && (

        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card max-w-sm w-full p-6 space-y-4">
            <h3 className="text-sm font-bold text-white">Add New Template Category</h3>
            <form onSubmit={handleAddCategoryToDb} className="space-y-4">
              <input
                type="text"
                placeholder="e.g. Engagement Ring, Pendant, etc."
                value={newCatName}
                onChange={(e) => setNewCatName(e.target.value)}
                className="w-full glass-input px-3 py-2 text-sm"
                required
              />
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowAddCatModal(false)}
                  className="btn-secondary px-3 py-1.5 text-xs"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary px-4 py-1.5 text-xs font-semibold">
                  Add Category
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Quick Add Subcategory Modal */}
      {showAddSubcatModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card max-w-sm w-full p-6 space-y-4">
            <h3 className="text-sm font-bold text-white">Add New Subcategory</h3>
            <form onSubmit={(e) => handleAddSubcategoryToDb(e, newSubcatCat)} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 font-semibold mb-1 block">Main Category:</label>
                <select
                  value={newSubcatCat || selectedHtmlCategory}
                  onChange={(e) => setNewSubcatCat(e.target.value)}
                  className="w-full glass-input px-3 py-2 text-sm text-purple-300 font-semibold"
                >
                  {dbCategories.map((c, idx) => (
                    <option key={idx} value={c.name} className="bg-gray-900 text-white">{c.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs text-gray-400 font-semibold mb-1 block">Subcategory Name:</label>
                <input
                  type="text"
                  placeholder="e.g. Solitaire, Halo, Vintage, Tennis, Cluster, etc."
                  value={newSubcatName}
                  onChange={(e) => setNewSubcatName(e.target.value)}
                  className="w-full glass-input px-3 py-2 text-sm"
                  required
                />
              </div>

              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowAddSubcatModal(false)}
                  className="btn-secondary px-3 py-1.5 text-xs"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary px-4 py-1.5 text-xs font-semibold">
                  Add Subcategory
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Quick Add Setting Column Modal */}
      {showAddColModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card max-w-sm w-full p-6 space-y-4">
            <h3 className="text-sm font-bold text-white">Add New Setting Column</h3>
            <form onSubmit={(e) => handleAddSettingColumnToDb(e, newColCat)} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 font-semibold mb-1 block">Category:</label>
                <select
                  value={newColCat || (templateCatFilter !== 'all' ? templateCatFilter : selectedHtmlCategory)}
                  onChange={(e) => setNewColCat(e.target.value)}
                  className="w-full glass-input px-3 py-2 text-xs"
                >
                  <option value="all" className="bg-gray-900">All Categories (Global)</option>
                  {dbCategories.map((c, idx) => (
                    <option key={idx} value={c.name} className="bg-gray-900">{c.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs text-gray-400 font-semibold mb-1 block">Setting Column Name:</label>
                <input
                  type="text"
                  placeholder="e.g. Default, Solitaire, Tennis, Eternity, 3 Stone, etc."
                  value={newColName}
                  onChange={(e) => setNewColName(e.target.value)}
                  className="w-full glass-input px-3 py-2 text-sm"
                  required
                />
              </div>

              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowAddColModal(false)}
                  className="btn-secondary px-3 py-1.5 text-xs"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary px-4 py-1.5 text-xs font-semibold">
                  Add Column
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Admin Password Unlock Modal */}
      {showAdminPassModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-card max-w-sm w-full p-6 space-y-4 border-rose-500/30">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center border border-rose-500/30">
                <i className="fa-solid fa-user-shield text-lg"></i>
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Unlock Admin Delete Mode</h3>
                <p className="text-xs text-gray-400">Enter password 0000 to enable delete options</p>
              </div>
            </div>

            <form onSubmit={handleAdminPassSubmit} className="space-y-4">
              <div>
                <input
                  type="password"
                  placeholder="Enter Admin Password"
                  value={adminPassInput}
                  onChange={(e) => setAdminPassInput(e.target.value)}
                  className="w-full glass-input px-3 py-2 text-sm text-center tracking-widest font-mono text-rose-200 border-rose-500/30 focus:border-rose-500"
                  autoFocus
                  required
                />
              </div>

              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowAdminPassModal(false)}
                  className="btn-secondary px-3 py-1.5 text-xs"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-1.5 text-xs font-semibold rounded-xl bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/30">
                  Unlock Deletions
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Save HTML Password Confirmation Modal */}
      {showSaveHtmlPassModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-card max-w-sm w-full p-6 space-y-4 border-indigo-500/40 shadow-2xl">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center border border-indigo-500/30">
                <i className="fa-solid fa-lock text-lg"></i>
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Password Confirmation Required</h3>
                <p className="text-xs text-gray-400">Enter password 0000 to save HTML to DB</p>
              </div>
            </div>

            <form onSubmit={executeSaveCompanyHtmlTemplate} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 font-semibold mb-1 block">
                  Target: <span className="text-indigo-300 font-bold">{selectedHtmlCompany}</span> ({selectedHtmlCategory} / {selectedHtmlSubcategory})
                </label>
                <input
                  type="password"
                  placeholder="Enter Password (0000)"
                  value={saveHtmlPassInput}
                  onChange={(e) => setSaveHtmlPassInput(e.target.value)}
                  className="w-full glass-input px-3 py-2 text-sm text-center tracking-widest font-mono text-indigo-200 border-indigo-500/40 focus:border-indigo-400"
                  autoFocus
                  required
                />
              </div>

              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowSaveHtmlPassModal(false)}
                  className="btn-secondary px-3 py-1.5 text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary px-4 py-1.5 text-xs font-bold flex items-center space-x-2"
                >
                  <i className="fa-solid fa-floppy-disk"></i>
                  <span>Confirm & Save</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Change Admin Password Modal */}
      {showChangePassModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-card max-w-sm w-full p-6 space-y-4 border-indigo-500/40 shadow-2xl">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center border border-indigo-500/30">
                <i className="fa-solid fa-key text-lg"></i>
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Change Admin Password</h3>
                <p className="text-xs text-gray-400">Update persistent password for Admin Mode</p>
              </div>
            </div>

            <form onSubmit={handleChangePasswordSubmit} className="space-y-3">
              <div>
                <label className="text-xs text-gray-400 font-semibold mb-1 block">Current Password:</label>
                <input
                  type="password"
                  placeholder="Enter current password"
                  value={changePassCurrent}
                  onChange={(e) => setChangePassCurrent(e.target.value)}
                  className="w-full glass-input px-3 py-2 text-xs font-mono text-indigo-200"
                  required
                  autoFocus
                />
              </div>

              <div>
                <label className="text-xs text-gray-400 font-semibold mb-1 block">New Password:</label>
                <input
                  type="password"
                  placeholder="Enter new password"
                  value={changePassNew}
                  onChange={(e) => setChangePassNew(e.target.value)}
                  className="w-full glass-input px-3 py-2 text-xs font-mono text-indigo-200"
                  required
                />
              </div>

              <div>
                <label className="text-xs text-gray-400 font-semibold mb-1 block">Confirm New Password:</label>
                <input
                  type="password"
                  placeholder="Confirm new password"
                  value={changePassConfirm}
                  onChange={(e) => setChangePassConfirm(e.target.value)}
                  className="w-full glass-input px-3 py-2 text-xs font-mono text-indigo-200"
                  required
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowChangePassModal(false)}
                  className="btn-secondary px-3 py-1.5 text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary px-4 py-1.5 text-xs font-bold flex items-center space-x-1.5"
                >
                  <i className="fa-solid fa-check"></i>
                  <span>Update Password</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Customize Navigation Bar Modal */}
      {showCustomizeNavModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="glass-card w-full max-w-lg p-6 space-y-4 rounded-2xl border border-indigo-500/40 shadow-2xl bg-slate-900/95 text-gray-200">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <i className="fa-solid fa-pen-to-square text-indigo-400"></i>
                <span>Customize Navigation Sidebar Titles</span>
              </h3>
              <button onClick={() => setShowCustomizeNavModal(false)} className="text-gray-400 hover:text-white p-1">
                <i className="fa-solid fa-xmark text-sm"></i>
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">1. Data Generator Tab Name:</label>
                <input
                  type="text"
                  value={tempNavLabels.generator || ''}
                  onChange={(e) => setTempNavLabels({ ...tempNavLabels, generator: e.target.value })}
                  placeholder="e.g. Data Generator Master"
                  className="w-full glass-input px-3 py-2 text-xs font-bold text-indigo-200"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">2. HTML App / Modifier Tab Name:</label>
                <input
                  type="text"
                  value={tempNavLabels.html_master || ''}
                  onChange={(e) => setTempNavLabels({ ...tempNavLabels, html_master: e.target.value })}
                  placeholder="e.g. HTML App (Modifier) Master"
                  className="w-full glass-input px-3 py-2 text-xs font-bold text-purple-200"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">3. Database Manager Tab Name:</label>
                <input
                  type="text"
                  value={tempNavLabels.database || ''}
                  onChange={(e) => setTempNavLabels({ ...tempNavLabels, database: e.target.value })}
                  placeholder="e.g. Database Manager Master"
                  className="w-full glass-input px-3 py-2 text-xs font-bold text-emerald-200"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">4. Excel Mapping Tab Name:</label>
                <input
                  type="text"
                  value={tempNavLabels.mapping || ''}
                  onChange={(e) => setTempNavLabels({ ...tempNavLabels, mapping: e.target.value })}
                  placeholder="e.g. Excel Mapping Master"
                  className="w-full glass-input px-3 py-2 text-xs font-bold text-amber-200"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">5. System Info / Settings Tab Name:</label>
                <input
                  type="text"
                  value={tempNavLabels.settings || ''}
                  onChange={(e) => setTempNavLabels({ ...tempNavLabels, settings: e.target.value })}
                  placeholder="e.g. System Info Master"
                  className="w-full glass-input px-3 py-2 text-xs font-bold text-blue-200"
                />
              </div>
            </div>

            <div className="flex justify-between items-center pt-3 border-t border-white/10">
              <button
                type="button"
                onClick={() => {
                  const defs = {
                    generator: 'Data Generator Master',
                    html_master: 'HTML App (Modifier) Master',
                    database: 'Database Manager Master',
                    mapping: 'Excel Mapping Master',
                    settings: 'System Info Master'
                  };
                  setTempNavLabels(defs);
                  setNavLabels(defs);
                  localStorage.removeItem('jewelry_app_nav_labels');
                  showToast('Navigation titles reset to default!', 'info');
                }}
                className="px-3 py-1.5 text-xs font-semibold rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10"
              >
                Reset Defaults
              </button>

              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={() => setShowCustomizeNavModal(false)}
                  className="btn-secondary px-3 py-1.5 text-xs"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setNavLabels(tempNavLabels);
                    localStorage.setItem('jewelry_app_nav_labels', JSON.stringify(tempNavLabels));
                    showToast('Navigation titles saved!', 'success');
                    setShowCustomizeNavModal(false);
                  }}
                  className="btn-primary px-4 py-1.5 text-xs font-bold"
                >
                  Save Navigation Titles
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Backup Modal with Description Field */}
      {showBackupCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="glass-card w-full max-w-md p-6 space-y-4 rounded-2xl border border-emerald-500/40 shadow-2xl bg-slate-900/95 text-gray-200">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-base font-bold text-emerald-300 flex items-center space-x-2">
                <i className="fa-solid fa-database text-emerald-400"></i>
                <span>Create Full Database Backup</span>
              </h3>
              <button onClick={() => setShowBackupCreateModal(false)} className="text-gray-400 hover:text-white p-1">
                <i className="fa-solid fa-xmark text-sm"></i>
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <label className="block font-semibold text-gray-300">
                Backup Description / Note (Optional):
              </label>
              <input
                type="text"
                value={backupDescriptionInput}
                onChange={(e) => setBackupDescriptionInput(e.target.value)}
                placeholder="e.g. Full backup before ring template update..."
                className="w-full glass-input px-3 py-2 text-xs text-emerald-200 focus:border-emerald-400"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    const descToSave = backupDescriptionInput;
                    setShowBackupCreateModal(false);
                    handleCreateDbBackup(descToSave);
                  }
                }}
              />
              <p className="text-[11px] text-gray-400">
                This description note will be stored with your timestamped SQLite backup file.
              </p>
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-white/10">
              <button
                type="button"
                onClick={() => setShowBackupCreateModal(false)}
                className="btn-secondary px-3.5 py-1.5 text-xs"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  const descToSave = backupDescriptionInput;
                  setShowBackupCreateModal(false);
                  handleCreateDbBackup(descToSave);
                }}
                className="px-4 py-1.5 text-xs font-bold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 rounded-xl shadow-lg flex items-center space-x-1.5 cursor-pointer"
              >
                <i className="fa-solid fa-download text-xs"></i>
                <span>Create Instant Backup</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* GUI Edit / Rename Modal */}
      {editModalConfig && (
        <EditModal
          config={editModalConfig}
          onClose={() => setEditModalConfig(null)}
        />
      )}

      {/* Floating Toast Notification */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 animate-bounce">
          <div className={`px-5 py-3 rounded-xl shadow-2xl flex items-center space-x-3 border backdrop-blur-md ${
            toast.type === 'success' ? 'bg-emerald-950/90 border-emerald-500/50 text-emerald-200' :
            toast.type === 'error' ? 'bg-rose-950/90 border-rose-500/50 text-rose-200' :
            toast.type === 'warning' ? 'bg-amber-950/90 border-amber-500/50 text-amber-200' :
            'bg-indigo-950/90 border-indigo-500/50 text-indigo-200'
          }`}>
            <i className={`fa-solid ${
              toast.type === 'success' ? 'fa-circle-check text-emerald-400' :
              toast.type === 'error' ? 'fa-circle-xmark text-rose-400' :
              toast.type === 'warning' ? 'fa-triangle-exclamation text-amber-400' :
              'fa-circle-info text-indigo-400'
            }`}></i>
            <span className="text-xs font-semibold">{toast.message}</span>
          </div>
        </div>
      )}
    </div>
  );
}

// GUI Edit / Rename Modal Component
function EditModal({ config, onClose }) {
  const [val, setVal] = useState(config.initialValue || '');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!val.trim()) return;
    setIsSubmitting(true);
    try {
      await config.onSave(val.trim());
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="glass-card max-w-sm w-full p-6 space-y-4 border-indigo-500/30">
        <div className="flex justify-between items-center pb-2 border-b border-white/10">
          <h3 className="text-sm font-bold text-white flex items-center space-x-2">
            <i className="fa-solid fa-pen-to-square text-indigo-400"></i>
            <span>{config.title}</span>
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <i className="fa-solid fa-xmark"></i>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs text-gray-400 font-semibold mb-1 block">{config.label}</label>
            <input
              type="text"
              value={val}
              onChange={(e) => setVal(e.target.value)}
              placeholder={config.placeholder || 'Enter value...'}
              className="w-full glass-input px-3 py-2 text-sm text-indigo-200 font-semibold focus:border-indigo-400"
              autoFocus
              required
            />
          </div>

          <div className="flex justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary px-3 py-1.5 text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary px-4 py-1.5 text-xs font-semibold"
            >
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Render React App
const rootElement = document.getElementById('root');
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(<App />);
}
