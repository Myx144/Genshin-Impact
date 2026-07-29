import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Material
import QtQuick.Dialogs
import Qt5Compat.GraphicalEffects

ApplicationWindow {
    id: window
    width: 1180
    height: 820
    minimumWidth: 1180
    maximumWidth: 1180
    minimumHeight: 820
    maximumHeight: 820
    visible: true
    flags: Qt.Window | Qt.FramelessWindowHint
    title: "原神伤害计算器"

    Material.theme: darkMode ? Material.Dark : Material.Light
    Material.accent: (themeColor("#a6a6a6", "#1a1a1a", "#55d7fa", "#30488f"))
    Material.primary: (themeColor("#202020", "#ffffff", "#0f1529", "#f8fbff"))
    color: themeColor("#202020", "#ffffff", "#0f1529", "#f8fbff")
    font.family: "Microsoft YaHei UI"

    // Poke-inspired tokens: compact, high-contrast frames and one quiet signal color.
    readonly property color signalBg: (themeColor("#202020", "#ffffff", "#0f1529", "#f8fbff"))
    readonly property color signalSurface: (themeColor("#252525", "#ffffff", "#192543", "#ffffff"))
    readonly property color signalLine: (themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2"))
    readonly property color signalText: (themeColor("#f1f1f1", "#1b1b1b", "#f3f7fd", "#18223e"))
    readonly property color signalMuted: (themeColor("#b7b7b7", "#616161", "#a7b6cf", "#62718c"))
    readonly property color signalAccent: (themeColor("#d0d0d0", "#151515", "#55d7fa", "#30488f"))
    readonly property color signalAccentSoft: (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff"))

    property var values: ({})
    property var slots: []
    property int currentSlot: 1
    property string slotName: ""
    property bool critDamageOnly: false
    property bool mainPctMode: false
    property int currentPage: 0
    property string currentDamageModule: "superconduct"
    property bool calculationModeMenuOpen: false
    property var damageModules: [
        {"id": "superconduct", "title": "星超导伤害", "subtitle": "SUPERCONDUCT DAMAGE", "enabled": true}
    ]
    readonly property string currentDamageModuleTitle: {
        for (let index = 0; index < damageModules.length; index++) {
            if (damageModules[index].id === currentDamageModule)
                return damageModules[index].title
        }
        return "星超导伤害"
    }
    property int pendingPage: 0
    property bool navigationButtonAtRight: false
    property int pendingSlot: 1
    property int slotDirection: 1
    property bool resultVisible: false
    property string lastError: ""
    property string statusMessage: "正在读取配置槽…"
    property bool autoSaveEnabled: true
    property bool darkMode: false
    property bool followSystemTheme: true
    property bool furinaTheme: false
    property bool themeTransitionRunning: false
    property int pendingThemeAction: 0
    property bool pendingDarkModeValue: false
    property color themeTransitionColor: "#151515"
    property real expectedDamage: 0
    property string displayedExpectedDamageText: "0"
    property string expectedDamageTargetText: "0"
    property int damageScrambleActiveDigit: 0
    property int damageScrambleRandomFrame: 0
    property int damageScrambleStage: 0
    property real damageScrambleElapsedMs: 0
    property real damageScrambleStepMs: 24
    property int damageScrambleRandomFrames: 3
    property var coefficients: ({})
    property var inputGroups: [
        {"title": "角色面板", "keys": ["atk", "em", "crit_rate", "crit_damage"]},
        {"title": "反应参数", "keys": ["talent_multiplier", "stacks", "reaction_bonus", "base_reaction_damage_bonus"]},
        {"title": "目标与附加", "keys": ["flat_damage_increase", "enemy_resistance", "elevation_bonus"]}
    ]
    property var conditionDefinitions: [
        {"key": "weapon_passive", "label": "武器特效 ATK%（不常驻）", "percent": true},
        {"key": "set_bonus", "label": "圣遗物套装 ATK%（不常驻）", "percent": true},
        {"key": "other_pct", "label": "其他 ATK%", "percent": true},
        {"key": "other_flat", "label": "其他固定 ATK", "percent": false}
    ]
    property var condBonuses: defaultConditionalBonuses()
    property var conditionalBonusKeys: [
        "weapon_passive_permanent", "set_bonus_permanent",
        "weapon_passive", "set_bonus", "other_pct", "other_flat"
    ]
    property real effectiveAtkValue: 0
    property bool effectiveAtkValid: true
    property real conditionalPercentValue: 0
    property real conditionalFlatValue: 0
    property var ugcCharacters: []
    property int ugcSelectedIndex: 0
    property var ugcRecognitionInfo: ({})
    property string ugcRecognitionError: ""
    property bool ugcRecognitionBusy: false
    property bool ugcWindowCaptureActive: false
    property bool sideMenuOpen: false
    property bool sideMenuTitlePushed: false
    property bool ugcImportedFieldsLocked: false
    property var ugcPreviousFieldValues: ({})

    function themeColor(defaultDark, defaultLight, furinaDark, furinaLight) {
        return furinaTheme
            ? (darkMode ? furinaDark : furinaLight)
            : (darkMode ? defaultDark : defaultLight)
    }

    function beginThemeTransition(action) {
        if (themeTransitionRunning)
            return
        pendingThemeAction = action
        themeTransitionColor = (furinaTheme || action === 2) ? "#5d7bb7" : "#808080"
        themeTransitionAnimation.start()
    }

    function setDarkModeAnimated(nextDarkMode) {
        const next = Boolean(nextDarkMode)
        if (themeTransitionRunning || darkMode === next)
            return
        pendingThemeAction = 1
        pendingDarkModeValue = next
        themeTransitionColor = furinaTheme ? "#5d7bb7" : "#808080"
        themeTransitionAnimation.start()
    }

    function applySystemTheme(animated) {
        if (!followSystemTheme)
            return
        const systemDark = Boolean(calculatorBridge.systemPrefersDark())
        if (animated)
            setDarkModeAnimated(systemDark)
        else
            darkMode = systemDark
    }

    function saveGlobalThemeSettings() {
        const response = JSON.parse(calculatorBridge.saveGlobalTheme(JSON.stringify({
            followSystem: followSystemTheme,
            darkMode: darkMode,
            furinaTheme: furinaTheme
        })))
        if (!response.ok)
            setStatusMessage("主题保存失败：" + response.error)
    }

    function loadGlobalThemeSettings() {
        const response = JSON.parse(calculatorBridge.loadGlobalTheme())
        if (!response.ok) {
            setStatusMessage("主题读取失败：" + response.error)
            return
        }
        restoreTheme(response.theme)
    }

    function setFollowSystemTheme(enabled) {
        const next = Boolean(enabled)
        if (followSystemTheme === next)
            return
        followSystemTheme = next
        saveGlobalThemeSettings()
        if (next)
            applySystemTheme(true)
    }

    function toggleThemeAnimated() {
        if (themeTransitionRunning)
            return
        if (followSystemTheme)
            followSystemTheme = false
        setDarkModeAnimated(!darkMode)
    }

    function toggleFurinaThemeAnimated() {
        beginThemeTransition(2)
    }

    function closeCalculationModeMenu() {
        calculationModeMenuOpen = false
    }

    function selectDamageModule(moduleId) {
        const nextModule = String(moduleId)
        if (nextModule !== "superconduct")
            return
        currentDamageModule = nextModule
        closeCalculationModeMenu()
        if (currentPage !== 0)
            showDamagePage()
    }

    function toggleSideMenu() {
        closeCalculationModeMenu()
        if (sideMenuDrawer.opened || sideMenuDrawer.position > 0) {
            // Start returning the title on the same input event as the drawer close.
            sideMenuTitlePushed = false
            sideMenuDrawer.close()
        } else {
            // Do not wait for Drawer.position to advance: the title starts immediately.
            sideMenuTitlePushed = true
            sideMenuDrawer.open()
        }
    }

    function compactSlotLabel(slot) {
        const name = String(slot.name || "").trim()
        const defaultName = "配置 " + slot.id
        if (name === "" || name === defaultName)
            return String(slot.id)
        return name.charAt(0)
    }

    function initializeValues() {
        const defaults = ({})
        for (let index = 0; index < inputFields.length; index++) {
            const field = inputFields[index]
            defaults[field.key] = field.defaultValue
        }
        values = defaults
    }

    function fieldDefinition(key) {
        for (let index = 0; index < inputFields.length; index++) {
            if (inputFields[index].key === key)
                return inputFields[index]
        }
        return {"key": key, "label": key, "required": "", "defaultValue": "0"}
    }

    function trimDecimalText(value) {
        let text = String(value).trim()
        if (text === "")
            return ""
        if (!/^-?(?:\d+\.?\d*|\.\d+)$/.test(text))
            return text
        if (text.indexOf(".") === -1)
            return text
        text = text.replace(/(\.\d*?[1-9])0+$/, "$1")
        text = text.replace(/\.0+$/, "")
        return text === "-0" ? "0" : text
    }

    function formatNumber(value, decimals) {
        const number = Number(value)
        if (!isFinite(number))
            return "—"
        return trimDecimalText(number.toFixed(decimals))
    }

    function setStatusMessage(message) {
        savedStatusTimer.stop()
        savedStatusFadeAnimation.stop()
        statusMessageLabel.opacity = 1
        statusMessage = message
        savedStatusTimer.interval = 2600
        savedStatusTimer.start()
    }

    function showSavedStatus(message) {
        savedStatusTimer.stop()
        savedStatusFadeAnimation.stop()
        statusMessageLabel.opacity = 1
        statusMessage = message
        savedStatusTimer.interval = 1800
        savedStatusTimer.start()
    }

    function setAutoSave(enabled) {
        autoSaveEnabled = enabled
        values["__auto_save__"] = enabled ? "True" : "False"
        saveCurrent(false)
    }

    function normalizeInputValues(source) {
        const normalized = ({})
        for (const key in source)
            normalized[key] = source[key]
        for (let index = 0; index < inputFields.length; index++) {
            const key = inputFields[index].key
            if (normalized[key] !== undefined)
                normalized[key] = trimDecimalText(normalized[key])
        }
        return normalized
    }

    function defaultConditionalBonuses() {
        return {
            "weapon_passive_permanent": {"value": "0", "enabled": true},
            "set_bonus_permanent": {"value": "0", "enabled": true},
            "weapon_passive": {"value": "0", "enabled": false},
            "set_bonus": {"value": "0", "enabled": false},
            "other_pct": {"value": "0", "enabled": false},
            "other_flat": {"value": "0", "enabled": false}
        }
    }

    function normalizeConditionalBonuses(source) {
        const normalized = defaultConditionalBonuses()
        if (source === undefined || source === null)
            return normalized
        for (let index = 0; index < conditionalBonusKeys.length; index++) {
            const key = conditionalBonusKeys[index]
            const entry = source[key]
            if (entry === undefined || entry === null)
                continue
            if (Array.isArray(entry)) {
                normalized[key] = {
                    "value": entry.length > 0 ? String(entry[0]) : "0",
                    "enabled": entry.length > 1 ? Boolean(entry[1]) : false
                }
            } else {
                normalized[key] = {
                    "value": entry.value !== undefined ? String(entry.value) : "0",
                    "enabled": Boolean(entry.enabled)
                }
            }
        }
        return normalized
    }

    function setConditionEnabled(key, enabled) {
        const next = normalizeConditionalBonuses(condBonuses)
        next[key].enabled = enabled
        condBonuses = next
        updateEffectiveAtk()
    }

    function commitConditionValue(key, value) {
        const next = normalizeConditionalBonuses(condBonuses)
        next[key].value = trimDecimalText(value)
        condBonuses = next
        updateEffectiveAtk()
    }

    function commitPermanentBonusValue(key, value) {
        const next = normalizeConditionalBonuses(condBonuses)
        next[key].value = trimDecimalText(value)
        next[key].enabled = true
        condBonuses = next
        updateEffectiveAtk()
    }

    function permanentBonusPercent(key) {
        const entry = condBonuses[key]
        const value = Number(entry === undefined ? 0 : (entry.value || 0))
        return mainPctMode ? value / 100.0 : value
    }

    function permanentWeaponPercent() {
        return permanentBonusPercent("weapon_passive_permanent")
    }

    function permanentSetBonusPercent() {
        return permanentBonusPercent("set_bonus_permanent")
    }

    function ugcPanelIncludesPermanentWeapon() {
        return String(values["__ugc_atk_includes_weapon_permanent__"] || "False") === "True"
    }

    function effectiveAtkSummary() {
        const panelAtk = Number(values["atk"] || 0)
        const baseAtk = Number(values["base_atk_input"] || 0)
        const permanentWeapon = permanentWeaponPercent()
        const permanentSetBonus = permanentSetBonusPercent()
        if (!isFinite(panelAtk) || !isFinite(baseAtk)
                || !isFinite(permanentWeapon) || !isFinite(permanentSetBonus))
            return {"valid": false, "effective": 0, "percent": 0, "flat": 0,
                    "panel": panelAtk, "base": baseAtk}

        let percent = permanentWeapon + permanentSetBonus
        let flat = 0
        for (let index = 0; index < conditionDefinitions.length; index++) {
            const definition = conditionDefinitions[index]
            const entry = condBonuses[definition.key]
            if (entry === undefined || !entry.enabled)
                continue
            const number = Number(entry.value || 0)
            if (!isFinite(number))
                return {"valid": false, "effective": 0, "percent": 0, "flat": 0,
                        "panel": panelAtk, "base": baseAtk}
            if (definition.percent)
                percent += mainPctMode ? number / 100.0 : number
            else
                flat += number
        }

        let panelBase = panelAtk
        if (ugcPanelIncludesPermanentWeapon()) {
            const importedWeaponPermanent = Number(values["__ugc_weapon_permanent_at_import__"] || 0)
            const importedSetPermanent = Number(values["__ugc_set_bonus_permanent_at_import__"] || 0)
            if (!isFinite(importedWeaponPermanent) || !isFinite(importedSetPermanent))
                return {"valid": false, "effective": 0, "percent": 0, "flat": 0,
                        "panel": panelAtk, "base": baseAtk}
            panelBase -= baseAtk * (importedWeaponPermanent + importedSetPermanent)
        }

        return {
            "valid": true,
            "effective": panelBase + baseAtk * percent + flat,
            "percent": percent,
            "flat": flat,
            "panel": panelAtk,
            "base": baseAtk
        }
    }

    function updateEffectiveAtk() {
        const summary = effectiveAtkSummary()
        effectiveAtkValid = summary.valid
        effectiveAtkValue = summary.effective
        conditionalPercentValue = summary.percent
        conditionalFlatValue = summary.flat
    }

    function commitInputValue(key, value) {
        const next = ({})
        for (const existingKey in values)
            next[existingKey] = values[existingKey]
        next[key] = trimDecimalText(value)
        if (key === "atk") {
            next["__ugc_atk_includes_weapon_permanent__"] = "False"
            next["__ugc_weapon_permanent_at_import__"] = "0"
            next["__ugc_set_bonus_permanent_at_import__"] = "0"
        }
        values = next
        if (key === "atk" || key === "base_atk_input")
            updateEffectiveAtk()
    }

    function reloadSlotList(loadCurrent) {
        const response = JSON.parse(calculatorBridge.listSlots())
        if (!response.ok) {
            setStatusMessage(response.error)
            return
        }
        slots = response.slots
        if (loadCurrent) {
            currentSlot = response.currentSlot
            loadSlot(currentSlot)
        }
    }

    function restoreTheme(theme) {
        if (!theme || typeof theme !== "object")
            return
        furinaTheme = Boolean(theme.furinaTheme)
        followSystemTheme = Boolean(theme.followSystem)
        if (followSystemTheme)
            applySystemTheme(false)
        else
            darkMode = Boolean(theme.darkMode)
    }

    function loadSlot(slot) {
        const response = JSON.parse(calculatorBridge.loadSlot(slot))
        if (!response.ok) {
            setStatusMessage(response.error)
            return
        }
        clearUgcFieldLock(false)
        currentSlot = slot
        values = normalizeInputValues(response.values)
        slotName = response.name
        Qt.callLater(function() {
            slotNameInput.cursorPosition = 0
            slotNameInput.deselect()
        })
        critDamageOnly = response.mode === "暴伤"
        mainPctMode = response.mainPctMode
        autoSaveEnabled = response.autoSave === undefined ? true : Boolean(response.autoSave)
        condBonuses = normalizeConditionalBonuses(response.condBonuses)
        updateEffectiveAtk()
        resultVisible = false
        lastError = ""
        setStatusMessage("已读取「" + slotName + "」")
        calculatorBridge.setCurrentSlot(slot)
    }

    function saveCurrent(showMessage) {
        values["__slot_name__"] = slotName.trim() === "" ? "配置 " + currentSlot : slotName.trim()
        values["__auto_save__"] = autoSaveEnabled ? "True" : "False"
        const response = JSON.parse(calculatorBridge.saveSlot(
            currentSlot,
            JSON.stringify({
                values: values,
                mode: critDamageOnly ? "暴伤" : "期望",
                mainPctMode: mainPctMode,
                condBonuses: condBonuses
            })
        ))
        if (!response.ok) {
            setStatusMessage(response.error)
            return false
        }
        slotName = values["__slot_name__"]
        reloadSlotList(false)
        if (showMessage)
            showSavedStatus("已保存「" + slotName + "」")
        return true
    }

    function switchSlot(slot) {
        if (slot === currentSlot || slotSwitchAnimation.running)
            return
        if (autoSaveEnabled && !saveCurrent(false))
            return
        pendingSlot = slot
        slotDirection = slot > currentSlot ? 1 : -1
        slotSwitchAnimation.start()
    }

    function requestPage(page) {
        if (page === currentPage || pageNavigationAnimation.running)
            return
        if (page === 1 && autoSaveEnabled && !saveCurrent(false))
            return
        pendingPage = page
        pageNavigationAnimation.start()
    }

    function showAtkPage() {
        requestPage(1)
    }

    function showDamagePage() {
        requestPage(0)
    }

    function applyAtkResult(atkValue, baseValue) {
        clearUgcFieldLock(false)
        const next = ({})
        for (const key in values)
            next[key] = values[key]
        next["atk"] = trimDecimalText(atkValue)
        next["base_atk_input"] = trimDecimalText(baseValue)
        next["__ugc_atk_includes_weapon_permanent__"] = "False"
        next["__ugc_weapon_permanent_at_import__"] = "0"
        next["__ugc_set_bonus_permanent_at_import__"] = "0"
        values = next
        updateEffectiveAtk()
        if (autoSaveEnabled)
            saveCurrent(false)
        setStatusMessage("已从 ATK 计算器应用角色 ATK")
        showDamagePage()
    }

    function isUgcRecognizedField(key) {
        return key === "atk" || key === "crit_rate" || key === "crit_damage"
            || key === "base_atk_input"
    }

    function clearUgcFieldLock(restoreValues) {
        if (restoreValues && ugcImportedFieldsLocked) {
            const restored = ({})
            for (const key in values)
                restored[key] = values[key]
            for (const key in ugcPreviousFieldValues)
                restored[key] = ugcPreviousFieldValues[key]
            values = restored
            updateEffectiveAtk()
            resultVisible = false
            lastError = ""
            if (autoSaveEnabled)
                saveCurrent(false)
            setStatusMessage("已撤销截图数据并恢复原值")
        }
        ugcImportedFieldsLocked = false
        ugcPreviousFieldValues = ({})
    }

    function cancelUgcImportedValues() {
        clearUgcFieldLock(true)
    }

    function recognizeUgcScreenshot(fileUrl) {
        if (ugcRecognitionBusy)
            return
        ugcRecognitionBusy = true
        ugcRecognitionError = ""
        setStatusMessage("正在识别 UGC 面板截图…")
        calculatorBridge.recognizeUgcScreenshotAsync(String(fileUrl))
    }

    function startUgcWindowCapture() {
        ugcCaptureModeDialog.close()
        ugcWindowCaptureActive = true
        setStatusMessage("请将鼠标移到游戏窗口并单击，右键或 Esc 可取消")
        window.hide()

        let response
        try {
            response = JSON.parse(calculatorBridge.startUgcWindowCapture())
        } catch (error) {
            response = {"ok": false, "error": "无法启动窗口截图"}
        }
        if (!response.ok) {
            ugcWindowCaptureActive = false
            window.show()
            window.raise()
            window.requestActivate()
            ugcRecognitionError = response.error || "无法启动窗口截图"
            ugcErrorDialog.open()
            setStatusMessage(ugcRecognitionError)
        }
    }

    function finishUgcWindowCapture(payload) {
        ugcWindowCaptureActive = false
        window.show()
        window.raise()
        window.requestActivate()

        let response
        try {
            response = JSON.parse(payload)
        } catch (error) {
            response = {"ok": false, "error": "窗口截图返回了无效结果"}
        }
        if (response.cancelled) {
            setStatusMessage("已取消窗口截图")
            return
        }
        if (!response.ok) {
            ugcRecognitionError = response.error || "窗口截图失败"
            ugcErrorDialog.open()
            setStatusMessage(ugcRecognitionError)
            return
        }

        const title = String(response.windowTitle || "游戏窗口")
        setStatusMessage("已截取「" + title + "」，正在识别…")
        recognizeUgcScreenshot(response.imageUrl)
    }

    function finishUgcRecognition(payload) {
        ugcRecognitionBusy = false
        let response
        try {
            response = JSON.parse(payload)
        } catch (error) {
            response = {"ok": false, "error": "截图识别返回了无效结果"}
        }
        if (!response.ok) {
            ugcRecognitionError = response.error || "UGC 截图识别失败"
            ugcErrorDialog.open()
            setStatusMessage(ugcRecognitionError)
            return
        }
        ugcCharacters = response.characters || []
        ugcSelectedIndex = 0
        ugcRecognitionInfo = response
        if (ugcCharacters.length === 0) {
            ugcRecognitionError = "截图中没有识别到角色数据"
            ugcErrorDialog.open()
            return
        }
        ugcResultDialog.open()
        setStatusMessage("已识别 " + ugcCharacters.length + " 个角色位置")
    }

    function applyUgcCharacter(character) {
        if (character === undefined || character.decoded === undefined)
            return
        const decoded = character.decoded
        if (!ugcImportedFieldsLocked) {
            ugcPreviousFieldValues = {
                "atk": values["atk"] !== undefined ? values["atk"] : "0",
                "base_atk_input": values["base_atk_input"] !== undefined
                    ? values["base_atk_input"] : "",
                "crit_rate": values["crit_rate"] !== undefined ? values["crit_rate"] : "0",
                "crit_damage": values["crit_damage"] !== undefined ? values["crit_damage"] : "0",
                "__ugc_atk_includes_weapon_permanent__":
                    values["__ugc_atk_includes_weapon_permanent__"] !== undefined
                        ? values["__ugc_atk_includes_weapon_permanent__"] : "False",
                "__ugc_weapon_permanent_at_import__":
                    values["__ugc_weapon_permanent_at_import__"] !== undefined
                        ? values["__ugc_weapon_permanent_at_import__"] : "0",
                "__ugc_set_bonus_permanent_at_import__":
                    values["__ugc_set_bonus_permanent_at_import__"] !== undefined
                        ? values["__ugc_set_bonus_permanent_at_import__"] : "0"
            }
        }
        const next = ({})
        for (const key in values)
            next[key] = values[key]
        next["atk"] = trimDecimalText(decoded.atk)
        next["base_atk_input"] = trimDecimalText(decoded.basic_atk)
        const displayFactor = mainPctMode ? 100.0 : 1.0
        next["crit_rate"] = formatNumber(Number(decoded.crit_rate) * displayFactor, 10)
        next["crit_damage"] = formatNumber(Number(decoded.crit_damage) * displayFactor, 10)
        const weaponPermanentAtImport = permanentWeaponPercent()
        const setPermanentAtImport = permanentSetBonusPercent()
        if (!isFinite(weaponPermanentAtImport) || !isFinite(setPermanentAtImport)) {
            setStatusMessage("武器或套装常驻 ATK% 不是有效数字")
            return
        }
        next["__ugc_atk_includes_weapon_permanent__"] = "True"
        next["__ugc_weapon_permanent_at_import__"] = formatNumber(weaponPermanentAtImport, 10)
        next["__ugc_set_bonus_permanent_at_import__"] = formatNumber(setPermanentAtImport, 10)
        values = next
        ugcImportedFieldsLocked = true
        updateEffectiveAtk()
        resultVisible = false
        lastError = ""
        if (autoSaveEnabled)
            saveCurrent(false)
        ugcResultDialog.close()
        setStatusMessage("已应用「" + character.name + "」面板数据")
    }

    function toggleDamageModeAnimated() {
        if (!modeTextAnimation.running)
            modeTextAnimation.start()
    }

    function valuesForCalculation() {
        const normalized = ({})
        for (const key in values)
            normalized[key] = values[key]
        if (!mainPctMode)
            return normalized

        const percentageKeys = [
            "crit_rate", "crit_damage", "talent_multiplier", "reaction_bonus",
            "base_reaction_damage_bonus", "enemy_resistance", "elevation_bonus"
        ]
        for (let index = 0; index < percentageKeys.length; index++) {
            const key = percentageKeys[index]
            const number = Number(normalized[key] || 0)
            normalized[key] = formatNumber(number / 100.0, 10)
        }
        return normalized
    }

    function digitCount(text) {
        let count = 0
        for (let index = 0; index < text.length; index++) {
            if (text.charAt(index) >= "0" && text.charAt(index) <= "9")
                count++
        }
        return count
    }

    function randomDigitExcept(targetCharacter) {
        const targetDigit = Number(targetCharacter)
        let randomDigit = Math.floor(Math.random() * 9)
        if (randomDigit >= targetDigit)
            randomDigit++
        return String(randomDigit)
    }

    function refreshScrambledDamageText() {
        let rendered = ""
        let digitIndex = 0
        for (let index = 0; index < expectedDamageTargetText.length; index++) {
            const character = expectedDamageTargetText.charAt(index)
            const isDigit = character >= "0" && character <= "9"
            if (!isDigit) {
                // Show punctuation only once the digit immediately after it starts rolling.
                if (digitIndex <= damageScrambleActiveDigit)
                    rendered += character
                continue
            }
            if (digitIndex < damageScrambleActiveDigit)
                rendered += character
            else if (digitIndex === damageScrambleActiveDigit)
                rendered += randomDigitExcept(character)
            else
                break
            digitIndex++
        }
        displayedExpectedDamageText = rendered
    }

    function animateExpectedDamage(targetValue) {
        damageScrambleFrameAnimation.stop()
        expectedDamageTargetText = formatNumber(Math.max(0, Number(targetValue) || 0), 5)
        const digits = Math.max(1, digitCount(expectedDamageTargetText))
        // Use the render loop rather than a coarse Timer. Three random frames per digit
        // stay below 0.6 s for normal damage values while matching the display refresh.
        const totalDuration = Math.min(560, Math.max(260, digits * 56))
        damageScrambleStepMs = totalDuration / (digits * damageScrambleRandomFrames)
        damageScrambleElapsedMs = 0
        damageScrambleStage = 0
        damageScrambleActiveDigit = 0
        damageScrambleRandomFrame = 0
        refreshScrambledDamageText()
        damageScrambleFrameAnimation.start()
    }

    function calculateDamage() {
        lastError = ""
        updateEffectiveAtk()
        if (!effectiveAtkValid) {
            lastError = "角色 ATK、白值或已启用的攻击力加成不是有效数字"
            resultVisible = false
            return
        }
        const calculationValues = valuesForCalculation()
        calculationValues["atk"] = formatNumber(effectiveAtkValue, 10)
        const payload = calculatorBridge.calculate(JSON.stringify(calculationValues), critDamageOnly)
        const response = JSON.parse(payload)
        if (!response.ok) {
            lastError = response.error
            resultVisible = false
            return
        }
        expectedDamage = response.expectedDamage
        coefficients = response.coefficients
        resultVisible = true
        animateExpectedDamage(expectedDamage)
        if (autoSaveEnabled)
            saveCurrent(false)
    }

    function toggleInputModeAnimated() {
        if (!inputModeTextAnimation.running)
            inputModeTextAnimation.start()
    }

    function toggleInputMode() {
        const factor = mainPctMode ? 0.01 : 100.0
        const percentageKeys = [
            "crit_rate", "crit_damage", "talent_multiplier", "reaction_bonus",
            "base_reaction_damage_bonus", "enemy_resistance", "elevation_bonus"
        ]
        const next = ({})
        for (const key in values)
            next[key] = values[key]
        for (let index = 0; index < percentageKeys.length; index++) {
            const key = percentageKeys[index]
            const number = Number(next[key] || 0)
            next[key] = formatNumber(number * factor, 10)
        }

        const nextConditions = normalizeConditionalBonuses(condBonuses)
        const percentConditionKeys = [
            "weapon_passive_permanent", "set_bonus_permanent",
            "weapon_passive", "set_bonus", "other_pct"
        ]
        for (let index = 0; index < percentConditionKeys.length; index++) {
            const key = percentConditionKeys[index]
            const number = Number(nextConditions[key].value || 0)
            nextConditions[key].value = formatNumber(number * factor, 10)
        }

        values = next
        condBonuses = nextConditions
        mainPctMode = !mainPctMode
        updateEffectiveAtk()
    }

    FrameAnimation {
        id: damageScrambleFrameAnimation
        running: false
        onTriggered: {
            damageScrambleElapsedMs += frameTime * 1000
            const nextStage = Math.floor(damageScrambleElapsedMs / damageScrambleStepMs)
            if (nextStage === damageScrambleStage)
                return
            damageScrambleStage = nextStage
            if (damageScrambleStage >= digitCount(expectedDamageTargetText) * damageScrambleRandomFrames) {
                displayedExpectedDamageText = expectedDamageTargetText
                stop()
                return
            }
            damageScrambleActiveDigit = Math.floor(damageScrambleStage / damageScrambleRandomFrames)
            damageScrambleRandomFrame = damageScrambleStage % damageScrambleRandomFrames
            refreshScrambledDamageText()
        }
    }

    onResultVisibleChanged: {
        if (!resultVisible) {
            damageScrambleFrameAnimation.stop()
            damageScrambleStage = 0
            damageScrambleElapsedMs = 0
            damageScrambleActiveDigit = 0
            damageScrambleRandomFrame = 0
            displayedExpectedDamageText = "0"
        }
    }

    SequentialAnimation {
        id: slotSwitchAnimation
        ParallelAnimation {
            NumberAnimation { target: damageContent; property: "opacity"; to: 0; duration: 120; easing.type: Easing.InCubic }
            NumberAnimation { target: slotTranslate; property: "x"; to: -42 * slotDirection; duration: 150; easing.type: Easing.InCubic }
        }
        ScriptAction {
            script: {
                loadSlot(pendingSlot)
                slotTranslate.x = 42 * slotDirection
            }
        }
        ParallelAnimation {
            NumberAnimation { target: damageContent; property: "opacity"; to: 1; duration: 170; easing.type: Easing.OutCubic }
            NumberAnimation { target: slotTranslate; property: "x"; to: 0; duration: 200; easing.type: Easing.OutCubic }
        }
    }

    SequentialAnimation {
        id: modeTextAnimation
        ParallelAnimation {
            NumberAnimation { target: modeBadgeText; property: "opacity"; to: 0; duration: 90 }
            NumberAnimation { target: modeBadgeTranslate; property: "y"; to: -8; duration: 110; easing.type: Easing.InCubic }
            NumberAnimation { target: modeResultLabel; property: "opacity"; to: 0; duration: 90 }
            NumberAnimation { target: modeResultTranslate; property: "y"; to: -8; duration: 110; easing.type: Easing.InCubic }
        }
        ScriptAction {
            script: {
                critDamageOnly = !critDamageOnly
                modeBadgeTranslate.y = 8
                modeResultTranslate.y = 8
            }
        }
        ParallelAnimation {
            NumberAnimation { target: modeBadgeText; property: "opacity"; to: 1; duration: 130 }
            NumberAnimation { target: modeBadgeTranslate; property: "y"; to: 0; duration: 160; easing.type: Easing.OutCubic }
            NumberAnimation { target: modeResultLabel; property: "opacity"; to: 1; duration: 130 }
            NumberAnimation { target: modeResultTranslate; property: "y"; to: 0; duration: 160; easing.type: Easing.OutCubic }
        }
    }

    SequentialAnimation {
        id: pageNavigationAnimation
        ScriptAction {
            script: {
                if (pendingPage === 0)
                    navigationButtonAtRight = false
            }
        }
        PauseAnimation { duration: pendingPage === 0 ? 260 : 0 }
        ParallelAnimation {
            NumberAnimation { target: pageNavigationText; property: "opacity"; to: 0; duration: 90 }
            NumberAnimation { target: pageNavigationTranslate; property: "y"; to: -8; duration: 110; easing.type: Easing.InCubic }
        }
        ScriptAction {
            script: {
                currentPage = pendingPage
                pageNavigationTranslate.y = 8
            }
        }
        ParallelAnimation {
            NumberAnimation { target: pageNavigationText; property: "opacity"; to: 1; duration: 130 }
            NumberAnimation { target: pageNavigationTranslate; property: "y"; to: 0; duration: 160; easing.type: Easing.OutCubic }
        }
        ScriptAction {
            script: {
                if (pendingPage === 1)
                    navigationButtonAtRight = true
            }
        }
    }

    SequentialAnimation {
        id: inputModeTextAnimation
        ParallelAnimation {
            NumberAnimation { target: inputModeButtonText; property: "opacity"; to: 0; duration: 90 }
            NumberAnimation { target: inputModeButtonTranslate; property: "y"; to: -7; duration: 105; easing.type: Easing.InCubic }
            NumberAnimation { target: inputModeHintText; property: "opacity"; to: 0; duration: 90 }
            NumberAnimation { target: inputModeHintTranslate; property: "y"; to: -7; duration: 105; easing.type: Easing.InCubic }
        }
        ScriptAction {
            script: {
                toggleInputMode()
                inputModeButtonTranslate.y = 7
                inputModeHintTranslate.y = 7
            }
        }
        ParallelAnimation {
            NumberAnimation { target: inputModeButtonText; property: "opacity"; to: 1; duration: 130 }
            NumberAnimation { target: inputModeButtonTranslate; property: "y"; to: 0; duration: 155; easing.type: Easing.OutCubic }
            NumberAnimation { target: inputModeHintText; property: "opacity"; to: 1; duration: 130 }
            NumberAnimation { target: inputModeHintTranslate; property: "y"; to: 0; duration: 155; easing.type: Easing.OutCubic }
        }
    }

    Timer {
        id: savedStatusTimer
        interval: 1800
        repeat: false
        onTriggered: savedStatusFadeAnimation.start()
    }

    SequentialAnimation {
        id: savedStatusFadeAnimation
        NumberAnimation {
            target: statusMessageLabel
            property: "opacity"
            to: 0
            duration: 260
            easing.type: Easing.InCubic
        }
        ScriptAction {
            script: {
                statusMessage = ""
                statusMessageLabel.opacity = 1
            }
        }
    }

    Component.onCompleted: {
        initializeValues()
        loadGlobalThemeSettings()
        reloadSlotList(true)
        applySystemTheme(false)
    }

    header: ToolBar {
        height: 64
        background: Rectangle { color: themeColor("#252525", "#f3f6fa", "#141d36", "#eef4fb") }

        Item {
            anchors.fill: parent

            // Frameless windows no longer have a native title bar. Drag the empty header area
            // to move the fixed-size window while leaving the controls above it clickable.
            DragHandler {
                target: null
                onActiveChanged: {
                    if (active)
                        window.startSystemMove()
                }
            }

            ColumnLayout {
                id: headerTitleBlock
                anchors.left: parent.left
                anchors.leftMargin: 68
                anchors.verticalCenter: parent.verticalCenter
                spacing: 0
                transform: Translate {
                    // Triggered by the menu action itself, so this starts before the drawer
                    // reaches the title instead of lagging behind the sliding handle.
                    x: sideMenuTitlePushed
                        ? Math.min(310, sideMenuDrawer.width + sideMenuHandle.width + 13
                            - headerTitleBlock.anchors.leftMargin)
                        : 0
                    Behavior on x {
                        NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
                    }
                }

                Label {
                    text: "原神伤害计算器"
                    font.pixelSize: 19
                    font.weight: Font.DemiBold
                    color: (themeColor("#e8e8e9", "#1b1b1b", "#f3f7fd", "#18223e"))
                }
                Label {
                    text: currentDamageModuleTitle
                    font.pixelSize: 11
                    color: (themeColor("#97979c", "#666666", "#8293ae", "#8795aa"))
                }
            }

            AppButton {
                id: pageNavigationButton
                width: 122
                height: 36
                anchors.verticalCenter: parent.verticalCenter
                x: parent.width - windowControls.width - 16 - width - (navigationButtonAtRight ? 0 : modeBadge.width + 14)
                onClicked: currentPage === 0 ? showAtkPage() : showDamagePage()

                Behavior on x {
                    NumberAnimation { duration: 260; easing.type: Easing.InOutCubic }
                }

                contentItem: Text {
                    id: pageNavigationText
                    anchors.fill: parent
                    text: currentPage === 0 ? "ATK 计算器" : "返回伤害计算"
                    transform: Translate { id: pageNavigationTranslate }
                    color: (themeColor("#e7e7e8", "#1b1b1b", "#f3f7fd", "#18223e"))
                    font.pixelSize: 11
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 3
                    color: pageNavigationButton.down
                        ? (themeColor("#252525", "#f2f2f2", "#344a72", "#eaf0f7"))
                        : (pageNavigationButton.hovered ? (themeColor("#2b2b2b", "#f7f7f7", "#2a3d63", "#f4f7fb")) : (themeColor("#202020", "#ffffff", "#0f1529", "#f8fbff")))
                    border.width: 1
                    border.color: pageNavigationButton.hovered ? (themeColor("#75757b", "#adadad", "#5874a3", "#9db3ce")) : (themeColor("#555555", "#e2e2e2", "#3a5077", "#d5e0ec"))
                    Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                    Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                }
            }

            Rectangle {
                id: modeBadge
                width: 138
                height: 36
                anchors.right: parent.right
                anchors.rightMargin: windowControls.width + 16
                anchors.verticalCenter: parent.verticalCenter
                radius: 3
                opacity: currentPage === 0 ? 1 : 0
                visible: opacity > 0
                transform: Translate {
                    y: currentPage === 0 ? 0 : -18
                    Behavior on y { NumberAnimation { duration: 190; easing.type: Easing.InCubic } }
                }
                color: modeBadgeMouse.containsMouse ? (themeColor("#333333", "#f7f7f7", "#2a3d63", "#f4f7fb")) : (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff"))
                border.width: 1
                border.color: modeBadgeMouse.containsMouse ? (themeColor("#75757b", "#adadad", "#5874a3", "#9db3ce")) : (themeColor("#555555", "#e2e2e2", "#3a5077", "#d5e0ec"))

                Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 160 } }
                Behavior on opacity { NumberAnimation { duration: 160 } }

                Text {
                    id: modeBadgeText
                    anchors.centerIn: parent
                    text: critDamageOnly ? "暴击伤害模式" : "期望伤害模式"
                    transform: Translate { id: modeBadgeTranslate }
                    color: (themeColor("#e7e7e8", "#1b1b1b", "#f3f7fd", "#18223e"))
                    font.pixelSize: 11
                }

                MouseArea {
                    id: modeBadgeMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: toggleDamageModeAnimated()
                }
            }


        }
    }

    Drawer {
        id: sideMenuDrawer
        parent: Overlay.overlay
        width: Math.min(300, Math.max(230, window.width * 0.27))
        height: window.height
        edge: Qt.LeftEdge
        modal: true
        dim: false
        interactive: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        enter: Transition {
            NumberAnimation {
                property: "position"
                duration: 260
                easing.type: Easing.OutCubic
            }
        }
        exit: Transition {
            NumberAnimation {
                property: "position"
                duration: 220
                easing.type: Easing.OutCubic
            }
        }

        onOpened: sideMenuOpen = true
        onAboutToHide: sideMenuTitlePushed = false
        onClosed: sideMenuOpen = false

        background: Rectangle {
            color: (themeColor("#252525", "#f3f6fa", "#141d36", "#eef4fb"))
            border.width: 1
            border.color: (themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2"))
        }

        contentItem: Item {
            Rectangle {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                height: 76
                color: themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff")

                Column {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: 18
                    anchors.rightMargin: 18
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 2

                    Label {
                        text: "原神伤害计算器"
                        color: themeColor("#f1f1f1", "#1b1b1b", "#f3f7fd", "#18223e")
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                    }
                    Label {
                        text: "GENSHIN DAMAGE CALCULATOR"
                        color: themeColor("#a8a8a8", "#666666", "#a7b6cf", "#62718c")
                        font.pixelSize: 9
                        font.letterSpacing: 1.1
                    }
                }

                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 1
                    color: themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2")
                }
            }

            Column {
                anchors.top: parent.top
                anchors.topMargin: 94
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.leftMargin: 18
                anchors.rightMargin: 18
                spacing: 10

                Item {
                    width: parent.width
                    height: 48

                    Label {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        text: "跟随系统"
                        color: themeColor("#f1f1f1", "#1b1b1b", "#f3f7fd", "#18223e")
                        font.pixelSize: 12
                    }

                    Rectangle {
                        id: followSystemThemeSwitch
                        width: 42
                        height: 22
                        radius: 11
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        color: followSystemTheme
                            ? (darkMode ? "#e8e8e8" : "#303030")
                            : themeColor("#4a4a4a", "#e2e2e2", "#3a5077", "#d7e3ef")

                        Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 180 } }

                        Rectangle {
                            width: 16
                            height: 16
                            radius: 8
                            y: 3
                            x: followSystemTheme ? 23 : 3
                            color: followSystemTheme ? (darkMode ? "#151515" : "#ffffff") : themeColor("#b7b7b7", "#ffffff", "#b1c0d7", "#ffffff")
                            Behavior on x { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
                            Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 180 } }
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        enabled: !themeTransitionRunning
                        onClicked: setFollowSystemTheme(!followSystemTheme)
                    }

                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 1
                        color: themeColor("#303030", "#deded9", "#304466", "#dee8f2")
                    }
                }

                Item {
                    width: parent.width
                    height: 48
                    opacity: followSystemTheme ? 0.52 : 1

                    Label {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        text: "深色模式"
                        color: themeColor("#f1f1f1", "#1b1b1b", "#f3f7fd", "#18223e")
                        font.pixelSize: 12
                    }

                    Rectangle {
                        id: themeSwitch
                        width: 42
                        height: 22
                        radius: 11
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        color: themeColor("#f1f1f1", "#e2e2e2", "#55d7fa", "#d7e3ef")

                        Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 180 } }

                        Rectangle {
                            width: 16
                            height: 16
                            radius: 8
                            y: 3
                            x: darkMode ? 23 : 3
                            color: themeColor("#151515", "#ffffff", "#0f1529", "#ffffff")
                            Behavior on x { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
                            Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 180 } }
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        enabled: !followSystemTheme && !themeTransitionRunning
                        onClicked: toggleThemeAnimated()
                    }

                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 1
                        color: themeColor("#303030", "#deded9", "#304466", "#dee8f2")
                    }
                }

                Item {
                    width: parent.width
                    height: 48

                    Label {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        text: "芙宁娜主题"
                        color: themeColor("#f1f1f1", "#1b1b1b", "#f3f7fd", "#18223e")
                        font.pixelSize: 12
                    }

                    Rectangle {
                        id: furinaThemeSwitch
                        width: 42
                        height: 22
                        radius: 11
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        color: furinaTheme
                            ? (darkMode ? "#55d7fa" : "#30488f")
                            : themeColor("#4a4a4a", "#e2e2e2", "#3a5077", "#d7e3ef")

                        Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 180 } }

                        Rectangle {
                            width: 16
                            height: 16
                            radius: 8
                            y: 3
                            x: furinaTheme ? 23 : 3
                            color: furinaTheme ? "#ffffff" : themeColor("#b7b7b7", "#ffffff", "#b1c0d7", "#ffffff")
                            Behavior on x { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
                            Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 180 } }
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        enabled: !themeTransitionRunning
                        onClicked: toggleFurinaThemeAnimated()
                    }

                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 1
                        color: themeColor("#303030", "#deded9", "#304466", "#dee8f2")
                    }
                }

                Repeater {
                    model: 2
                    delegate: Item {
                        width: parent.width
                        height: 44

                        Rectangle {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            height: 1
                            color: themeColor("#303030", "#deded9", "#304466", "#dee8f2")
                        }
                    }
                }
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: developerCredit.top
                anchors.leftMargin: 18
                anchors.rightMargin: 18
                height: 1
                color: themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2")
            }

            Label {
                id: developerCredit
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.leftMargin: 18
                anchors.rightMargin: 18
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 16
                text: "Developed by  Myx144"
                color: themeColor("#909090", "#777777", "#8293ae", "#8795aa")
                font.pixelSize: 9
                font.letterSpacing: 0.5
                horizontalAlignment: Text.AlignLeft
            }
        }
    }

    MouseArea {
        id: calculationModeDismissArea
        parent: Overlay.overlay
        anchors.fill: parent
        z: sideMenuDrawer.z + 7
        visible: calculationModeMenuOpen
        enabled: visible
        onClicked: closeCalculationModeMenu()
    }

    Item {
        id: calculationModeDropPanel
        parent: Overlay.overlay
        property bool animationReady: false
        property real panelHeight: calculationModeColumn.implicitHeight
        x: Math.round((parent.width - width) / 2)
        y: calculationModeMenuOpen ? 0 : -panelHeight
        width: 236
        height: panelHeight + calculationModeButton.height
        z: sideMenuDrawer.z + 8
        visible: !ugcResultDialog.visible && !ugcErrorDialog.visible && !ugcLoadingOverlay.visible

        Component.onCompleted: animationReady = true
        onVisibleChanged: {
            if (!visible)
                closeCalculationModeMenu()
        }

        Behavior on y {
            enabled: calculationModeDropPanel.animationReady
            NumberAnimation {
                duration: calculationModeMenuOpen ? 250 : 210
                easing.type: Easing.OutCubic
            }
        }

        Rectangle {
            id: calculationModeMenuSurface
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: calculationModeDropPanel.panelHeight
            radius: 4
            color: themeColor("#252525", "#ffffff", "#192543", "#ffffff")
            border.width: 1
            border.color: themeColor("#4a4a4a", "#d8d8d8", "#3a5077", "#d5e0ec")

            Column {
                id: calculationModeColumn
                anchors.fill: parent

                Rectangle {
                    width: parent.width
                    height: 38
                    color: themeColor("#2b2b2b", "#f7f7f7", "#1e2c4d", "#dceff7")

                    Label {
                        anchors.left: parent.left
                        anchors.leftMargin: 14
                        anchors.verticalCenter: parent.verticalCenter
                        text: "切换计算模式"
                        color: themeColor("#f1f1f1", "#1b1b1b", "#f3f7fd", "#18223e")
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                    }
                }

                Repeater {
                    model: damageModules
                    delegate: Rectangle {
                        id: damageModuleItem
                        required property var modelData
                        property bool selected: modelData.id === currentDamageModule
                        width: calculationModeColumn.width
                        height: 52
                        color: selected
                            ? themeColor("#343434", "#f1f1f1", "#223b69", "#e1f7fe")
                            : (damageModuleMouse.containsMouse
                                ? themeColor("#303030", "#f7f7f7", "#2a3d63", "#f4f7fb")
                                : "transparent")
                        opacity: modelData.enabled ? 1 : 0.48

                        Column {
                            anchors.left: parent.left
                            anchors.leftMargin: 14
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 1
                            Label {
                                text: modelData.title
                                color: themeColor("#f1f1f1", "#1b1b1b", "#f3f7fd", "#18223e")
                                font.pixelSize: 12
                                font.weight: damageModuleItem.selected ? Font.DemiBold : Font.Normal
                            }
                            Label {
                                text: modelData.subtitle
                                color: themeColor("#909095", "#666666", "#8293ae", "#8795aa")
                                font.pixelSize: 8
                                font.letterSpacing: 0.7
                            }
                        }

                        Label {
                            anchors.right: parent.right
                            anchors.rightMargin: 14
                            anchors.verticalCenter: parent.verticalCenter
                            text: damageModuleItem.selected ? "当前" : ""
                            color: themeColor("#b7b7bb", "#505050", "#55d7fa", "#30488f")
                            font.pixelSize: 9
                        }

                        MouseArea {
                            id: damageModuleMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: modelData.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                            enabled: modelData.enabled
                            onClicked: selectDamageModule(modelData.id)
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    height: 34
                    color: "transparent"
                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        height: 1
                        color: themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2")
                    }
                    Label {
                        anchors.centerIn: parent
                        text: "后续伤害模块将在此处显示"
                        color: themeColor("#88888c", "#777777", "#8293ae", "#8795aa")
                        font.pixelSize: 9
                    }
                }
            }
        }

        Item {
            id: calculationModeButton
            x: Math.round((parent.width - width) / 2)
            y: calculationModeDropPanel.panelHeight - 1
            width: 112
            height: 22

            property color fillColor: calculationModeMouse.pressed
                ? themeColor("#343434", "#ededed", "#344a72", "#eaf0f7")
                : (calculationModeMouse.containsMouse
                    ? themeColor("#303030", "#f5f5f5", "#2a3d63", "#f4f7fb")
                    : themeColor("#292929", "#ffffff", "#192543", "#ffffff"))
            property color outlineColor: calculationModeMouse.containsMouse
                ? themeColor("#737373", "#a8a8a8", "#5874a3", "#9db3ce")
                : themeColor("#4a4a4a", "#d8d8d8", "#3a5077", "#d5e0ec")
            property color iconColor: themeColor("#eeeeee", "#252525", "#55d7fa", "#30488f")

            onFillColorChanged: calculationModeCanvas.requestPaint()
            onOutlineColorChanged: calculationModeCanvas.requestPaint()
            onIconColorChanged: calculationModeCanvas.requestPaint()

            Canvas {
                id: calculationModeCanvas
                anchors.fill: parent
                antialiasing: true
                onPaint: {
                    const context = getContext("2d")
                    context.reset()
                    context.beginPath()
                    context.moveTo(0.5, 0.5)
                    context.lineTo(width - 0.5, 0.5)
                    context.lineTo(width - 15.5, height - 0.5)
                    context.lineTo(15.5, height - 0.5)
                    context.closePath()
                    context.fillStyle = calculationModeButton.fillColor
                    context.fill()
                    context.strokeStyle = calculationModeButton.outlineColor
                    context.lineWidth = 1
                    context.stroke()

                    const centerX = width / 2
                    const centerY = height / 2 + 1
                    context.beginPath()
                    context.moveTo(centerX - 4.5, centerY - 2.5)
                    context.lineTo(centerX + 4.5, centerY - 2.5)
                    context.lineTo(centerX, centerY + 3.5)
                    context.closePath()
                    context.fillStyle = calculationModeButton.iconColor
                    context.fill()
                }
            }

            MouseArea {
                id: calculationModeMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    if (sideMenuDrawer.opened)
                        sideMenuDrawer.close()
                    calculationModeMenuOpen = !calculationModeMenuOpen
                }
            }
        }
    }

    Row {
        id: windowControls
        parent: Overlay.overlay
        anchors.top: parent.top
        anchors.right: parent.right
        height: 64
        width: 96
        spacing: 0
        z: sideMenuDrawer.z + 12
        visible: !ugcResultDialog.visible && !ugcErrorDialog.visible && !ugcLoadingOverlay.visible

        Rectangle {
            id: minimizeWindowButton
            width: 48
            height: parent.height
            color: minimizeWindowMouse.containsMouse
                ? themeColor("#383838", "#e7e7e7", "#223253", "#e8f3fb")
                : "transparent"

            Text {
                anchors.centerIn: parent
                anchors.verticalCenterOffset: -2
                text: "−"
                color: themeColor("#e7e7e8", "#1b1b1b", "#f3f7fd", "#18223e")
                font.pixelSize: 20
                font.weight: Font.Medium
            }

            MouseArea {
                id: minimizeWindowMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: window.showMinimized()
            }
        }

        Rectangle {
            id: closeWindowButton
            width: 48
            height: parent.height
            color: closeWindowMouse.pressed
                ? "#a8261a"
                : (closeWindowMouse.containsMouse ? "#c42b1c" : "transparent")

            Text {
                anchors.centerIn: parent
                anchors.verticalCenterOffset: -1
                text: "×"
                color: closeWindowMouse.containsMouse
                    ? "#ffffff"
                    : themeColor("#e7e7e8", "#1b1b1b", "#f3f7fd", "#18223e")
                font.pixelSize: 22
                font.weight: Font.Light
            }

            MouseArea {
                id: closeWindowMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: window.close()
            }
        }
    }

    Rectangle {
        id: sideMenuHandle
        parent: Overlay.overlay
        // Drawer.position is 0 when closed and 1 when open, including its slide animation.
        x: sideMenuDrawer.position * (sideMenuDrawer.width - 1)
        y: 0
        width: 58
        height: 64
        z: sideMenuDrawer.z + 10
        visible: !ugcResultDialog.visible && !ugcErrorDialog.visible && !ugcLoadingOverlay.visible
        color: (themeColor("#252525", "#f3f6fa", "#141d36", "#eef4fb"))
        border.width: 1
        border.color: (themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2"))

        Column {
            anchors.centerIn: parent
            spacing: 4

            Repeater {
                model: 3
                delegate: Rectangle {
                    width: 15
                    height: 1
                    radius: 1
                    color: (themeColor("#eaeaea", "#151515", "#f3f7fd", "#18223e"))
                }
            }
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: toggleSideMenu()
        }
    }

    DropShadow {
        id: sideMenuHandleShadow
        parent: Overlay.overlay
        anchors.fill: sideMenuHandle
        source: sideMenuHandle
        horizontalOffset: 3
        verticalOffset: 3
        radius: 6
        samples: 9
        color: (darkMode ? "#28000000" : "#28000000")
        cached: true
        transparentBorder: true
        // The tab is flat while the sidebar is closed; its shadow fades in only with the drawer.
        visible: sideMenuHandle.visible && sideMenuDrawer.position > 0.001
        opacity: sideMenuDrawer.position
        z: sideMenuHandle.z - 1
    }

    Rectangle {
        id: sideMenuShadow
        parent: Overlay.overlay
        x: sideMenuHandle.x + 1
        y: 0
        width: 24
        height: sideMenuDrawer.height
        z: sideMenuDrawer.z - 1
        visible: sideMenuDrawer.visible
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: (darkMode ? "#26000000" : "#26000000") }
            GradientStop { position: 1.0; color: "#00000000" }
        }
    }

    Rectangle {
        id: damagePage
        anchors.fill: parent
        z: currentPage === 0 ? 2 : 1
        enabled: currentPage === 0
        visible: opacity > 0
        opacity: currentPage === 0 ? 1 : 0
        color: (themeColor("#202020", "#ffffff", "#0f1529", "#f8fbff"))

        Repeater {
            model: 12
            delegate: Rectangle {
                width: 1
                height: parent.height
                x: index * parent.width / 12
                color: (themeColor("#d6d6d8", "#323232", "#b1c0d7", "#5f6f89"))
                opacity: 0.018
            }
        }

        transform: Translate {
            y: currentPage === 0 ? 0 : -48
            Behavior on y { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }
        }
        Behavior on opacity { NumberAnimation { duration: 210; easing.type: Easing.OutCubic } }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 10

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 52
                radius: 3
                color: (themeColor("#252525", "#ffffff", "#192543", "#ffffff"))
                border.width: 1
                border.color: (themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2"))

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14
                    spacing: 8

                    Label {
                        text: "CONFIG"
                        color: (themeColor("#b7b7bb", "#505050", "#b1c0d7", "#5f6f89"))
                        font.pixelSize: 12
                    }

                    Repeater {
                        model: slots
                        delegate: AppButton {
                            id: slotButton
                            required property var modelData
                            property bool current: modelData.id === currentSlot
                            Layout.preferredHeight: 36
                            Layout.preferredWidth: 54
                            onClicked: switchSlot(modelData.id)

                            contentItem: Text {
                                id: slotText
                                anchors.fill: parent
                                anchors.margins: 4
                                text: compactSlotLabel(modelData)
                                color: slotButton.current ? (themeColor("#f5f5f5", "#ffffff", "#ffffff", "#ffffff")) : (themeColor("#c7c7ca", "#383835", "#b1c0d7", "#5f6f89"))
                                font.pixelSize: 12
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                elide: Text.ElideRight
                            }
                            background: Rectangle {
                                radius: 3
                                color: slotButton.current
                                    ? (slotButton.hovered ? (themeColor("#555555", "#3b3b3b", "#4d6fc3", "#3d5caa")) : (themeColor("#4a4a4a", "#323232", "#3d5caa", "#30488f")))
                                    : (slotButton.down
                                        ? (themeColor("#383838", "#f2f2f2", "#344a72", "#eaf0f7"))
                                        : (slotButton.hovered ? (themeColor("#333333", "#f7f7f7", "#2a3d63", "#f4f7fb")) : (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff"))))
                                border.width: 1
                                border.color: slotButton.current
                                    ? (slotButton.hovered ? (themeColor("#787878", "#444444", "#6a89ba", "#3d5caa")) : (themeColor("#686868", "#2a2a2a", "#5874a3", "#263a77")))
                                    : (slotButton.hovered ? (themeColor("#5a5a5a", "#adadad", "#5874a3", "#9db3ce")) : (themeColor("#4a4a4a", "#d5d5d5", "#3a5077", "#cfdceb")))
                                Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 120 } }
                                Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 120 } }
                            }
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: 1
                        Layout.preferredHeight: 28
                        color: (themeColor("#4a4a4a", "#d5d5d5", "#3a5077", "#cfdceb"))
                    }

                    Label {
                        text: "NAME"
                        color: (themeColor("#97979c", "#666666", "#8293ae", "#8795aa"))
                        font.pixelSize: 11
                    }

                    TextField {
                        id: slotNameInput
                        objectName: "slotNameInput"
                        Layout.preferredWidth: 145
                        Layout.preferredHeight: 33
                        text: slotName
                        selectByMouse: true
                        placeholderText: ""
                        leftPadding: 10
                        rightPadding: 10
                        color: (themeColor("#e1e1e3", "#1b1b1b", "#f3f7fd", "#18223e"))
                        onTextChanged: {
                            if (!activeFocus) {
                                cursorPosition = 0
                                deselect()
                            }
                        }
                        onTextEdited: slotName = text
                        onEditingFinished: {
                            if (autoSaveEnabled)
                                saveCurrent(false)
                        }
                        background: Rectangle {
                            radius: 3
                            color: slotNameInput.activeFocus ? (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff")) : (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff"))
                            border.width: 1
                            border.color: slotNameInput.activeFocus ? (themeColor("#707070", "#7a7a7a", "#62bfe8", "#5478b5")) : (themeColor("#4a4a4a", "#d5d5d5", "#3a5077", "#cfdceb"))
                            Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 120 } }
                            Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 120 } }
                        }
                    }

                    AppButton {
                        id: slotSaveButton
                        Layout.preferredWidth: 84
                        Layout.preferredHeight: 36
                        onClicked: saveCurrent(true)
                        contentItem: Text {
                            anchors.fill: parent
                            anchors.margins: 4
                            text: "保存"
                            color: (themeColor("#f5f5f5", "#ffffff", "#ffffff", "#ffffff"))
                            font.pixelSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            radius: 3
                            color: slotSaveButton.down
                                ? (themeColor("#606060", "#454545", "#5b7ed0", "#263a77"))
                                : (slotSaveButton.hovered ? (themeColor("#555555", "#3b3b3b", "#4d6fc3", "#3d5caa")) : (themeColor("#4a4a4a", "#323232", "#3d5caa", "#30488f")))
                            border.width: 1
                            border.color: slotSaveButton.hovered ? (themeColor("#787878", "#444444", "#6a89ba", "#3d5caa")) : (themeColor("#686868", "#2a2a2a", "#5874a3", "#263a77"))
                            Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                            Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                        }
                    }

                    AppCheckBox {
                        id: autoSaveCheckBox
                        Layout.preferredWidth: 94
                        Layout.preferredHeight: 34
                        text: "自动保存"
                        checked: autoSaveEnabled
                        font.pixelSize: 10
                        onToggled: setAutoSave(checked)
                    }

                    Item { Layout.fillWidth: true }
                    Label {
                        id: statusMessageLabel
                        visible: window.width >= 1080
                        text: statusMessage
                        color: (themeColor("#909095", "#616161", "#8293ae", "#5f6f89"))
                        font.pixelSize: 11
                        Layout.preferredWidth: visible ? 118 : 0
                        Layout.maximumWidth: 118
                        Layout.minimumWidth: 0
                        horizontalAlignment: Text.AlignRight
                        elide: Text.ElideRight
                        clip: true
                    }
                }
            }

            RowLayout {
                id: damageContent
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 18
                opacity: 1
                transform: Translate { id: slotTranslate }

                Rectangle {
                    Layout.preferredWidth: 510
                    Layout.fillHeight: true
                    radius: 3
                    color: (themeColor("#252525", "#ffffff", "#192543", "#ffffff"))
                    border.width: 1
                    border.color: (themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2"))

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            Label {
                                text: "输入数据"
                                font.pixelSize: 16
                                font.weight: Font.DemiBold
                                color: (themeColor("#dfdfe1", "#20201e", "#f3f7fd", "#18223e"))
                            }
                            Item { Layout.fillWidth: true }
                            AppButton {
                                id: ugcImportButton
                                Layout.preferredWidth: 94
                                Layout.preferredHeight: 34
                                enabled: !ugcRecognitionBusy && !ugcWindowCaptureActive
                                onClicked: ugcCaptureModeDialog.open()
                                contentItem: Text {
                                    anchors.fill: parent
                                    text: "截图识别"
                                    color: (themeColor("#d6d6d8", "#323232", "#b1c0d7", "#5f6f89"))
                                    font.pixelSize: 11
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    radius: 3
                                    color: ugcImportButton.down
                                        ? (themeColor("#252525", "#f2f2f2", "#344a72", "#eaf0f7"))
                                        : (ugcImportButton.hovered ? (themeColor("#383838", "#f7f7f7", "#2a3d63", "#f4f7fb")) : (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff")))
                                    border.width: 1
                                    border.color: ugcImportButton.hovered ? (themeColor("#707076", "#adadad", "#5874a3", "#9db3ce")) : (themeColor("#5b5b61", "#c0c0c0", "#3a5077", "#cfdceb"))
                                    Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                                    Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                                }
                            }
                            AppButton {
                                id: cancelUgcImportButton
                                visible: ugcImportedFieldsLocked
                                Layout.preferredWidth: visible ? 88 : 0
                                Layout.preferredHeight: 34
                                text: "撤销识别"
                                onClicked: cancelUgcImportedValues()
                                contentItem: Text {
                                    text: cancelUgcImportButton.text
                                    color: (themeColor("#f5f5f5", "#ffffff", "#ffffff", "#ffffff"))
                                    font.pixelSize: 11
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    radius: 3
                                    color: cancelUgcImportButton.down
                                        ? (themeColor("#606060", "#454545", "#5b7ed0", "#263a77"))
                                        : (cancelUgcImportButton.hovered ? (themeColor("#555555", "#3b3b3b", "#4d6fc3", "#3d5caa")) : (themeColor("#4a4a4a", "#323232", "#3d5caa", "#30488f")))
                                    border.width: 1
                                    border.color: (themeColor("#686868", "#2a2a2a", "#5874a3", "#263a77"))
                                }
                            }
                            AppButton {
                                id: mainInputModeButton
                                Layout.preferredWidth: 104
                                Layout.preferredHeight: 34
                                enabled: !ugcImportedFieldsLocked
                                onClicked: toggleInputModeAnimated()
                                contentItem: Text {
                                    id: inputModeButtonText
                                    anchors.fill: parent
                                    anchors.margins: 4
                                    text: mainPctMode === true ? "百分数输入" : "小数输入"
                                    transform: Translate { id: inputModeButtonTranslate }
                                    color: (themeColor("#dddddf", "#222220", "#dbe5f3", "#24304a"))
                                    font.pixelSize: 11
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    radius: 3
                                    color: mainInputModeButton.down
                                        ? (themeColor("#252525", "#f2f2f2", "#344a72", "#eaf0f7"))
                                        : (mainInputModeButton.hovered ? (themeColor("#383838", "#f7f7f7", "#2a3d63", "#f4f7fb")) : (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff")))
                                    border.width: 1
                                    border.color: mainInputModeButton.hovered ? (themeColor("#707076", "#adadad", "#5874a3", "#9db3ce")) : (themeColor("#5b5b61", "#c0c0c0", "#3a5077", "#cfdceb"))
                                    Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                                    Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                                }
                            }
                        }

                        Label {
                            id: inputModeHintText
                            text: mainPctMode ? "百分比使用 70 这样的数字输入" : "百分比使用 0.7 这样的数字输入"
                            transform: Translate { id: inputModeHintTranslate }
                            font.pixelSize: 11
                            color: (themeColor("#909095", "#616161", "#8293ae", "#5f6f89"))
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignTop
                            spacing: 7

                            Repeater {
                                model: inputGroups

                                delegate: ColumnLayout {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    spacing: 5

                                    Label {
                                        text: modelData.title
                                        color: (themeColor("#a8a8ad", "#575752", "#a7b6cf", "#62718c"))
                                        font.pixelSize: 11
                                        font.weight: Font.DemiBold
                                        leftPadding: 2
                                    }

                                    GridLayout {
                                        Layout.fillWidth: true
                                        columns: 2
                                        columnSpacing: 9
                                        rowSpacing: 5

                                        Repeater {
                                            model: modelData.keys

                                            delegate: Rectangle {
                                                id: fieldBox
                                                required property string modelData
                                                property var fieldData: window.fieldDefinition(modelData)
                                                objectName: "mainField_" + fieldData.key
                                                property bool ugcLocked: ugcImportedFieldsLocked
                                                    && isUgcRecognizedField(fieldData.key)
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: 50
                                                radius: 3
                                                color: ugcLocked ? (themeColor("#303030", "#f2f2f2", "#1e2c4d", "#edf3f9")) : (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff"))
                                                border.width: 1
                                                border.color: ugcLocked
                                                    ? (themeColor("#3a3a3a", "#ddddda", "#304466", "#d7e3ef"))
                                                    : (input.activeFocus ? (themeColor("#707070", "#7a7a7a", "#62bfe8", "#5478b5")) : (themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2")))

                                                Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 120 } }
                                                Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 120 } }

                                                Label {
                                                    anchors.left: parent.left
                                                    anchors.top: parent.top
                                                    anchors.leftMargin: 10
                                                    anchors.topMargin: 5
                                                    text: fieldData.label
                                                    font.pixelSize: 11
                                                    color: (themeColor("#d3d3d6", "#2c2c29", "#b1c0d7", "#5f6f89"))
                                                    width: parent.width - 76
                                                    elide: Text.ElideRight
                                                }

                                                Label {
                                                    anchors.right: parent.right
                                                    anchors.top: parent.top
                                                    anchors.rightMargin: 9
                                                    anchors.topMargin: 7
                                                    text: fieldData.required
                                                    font.pixelSize: 9
                                                    color: (themeColor("#8b8b90", "#727272", "#8293ae", "#8795aa"))
                                                }

                                                TextInput {
                                                    id: input
                                                    objectName: "mainInput_" + fieldData.key
                                                    anchors.left: parent.left
                                                    anchors.right: parent.right
                                                    anchors.bottom: parent.bottom
                                                    anchors.leftMargin: 10
                                                    anchors.rightMargin: 10
                                                    anchors.bottomMargin: 5
                                                    height: 20
                                                    text: values[fieldData.key] !== undefined
                                                        ? String(values[fieldData.key])
                                                        : String(fieldData.defaultValue)
                                                    enabled: !fieldBox.ugcLocked
                                                    opacity: enabled ? 1 : 0.52
                                                    selectByMouse: enabled
                                                    clip: true
                                                    color: (themeColor("#e7e7e8", "#1b1b1b", "#f3f7fd", "#18223e"))
                                                    selectionColor: (themeColor("#dfdfdf", "#202020", "#55d7fa", "#30488f"))
                                                    selectedTextColor: (themeColor("#202020", "#ffffff", "#0f1529", "#f8fbff"))
                                                    font.pixelSize: 13
                                                    verticalAlignment: TextInput.AlignVCenter
                                                    onTextEdited: {
                                                        values[fieldData.key] = text
                                                        if (fieldData.key === "atk")
                                                            updateEffectiveAtk()
                                                    }
                                                    onActiveFocusChanged: {
                                                        if (!activeFocus)
                                                            commitInputValue(fieldData.key, text)
                                                    }
                                                }

                                                MouseArea {
                                                    anchors.fill: input
                                                    acceptedButtons: Qt.NoButton
                                                    hoverEnabled: true
                                                    cursorShape: Qt.IBeamCursor
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        Rectangle {
                            id: conditionBonusPanel
                            Layout.fillWidth: true
                            // Three dense rows need 140 px after margins; keep a small
                            // safety gap so the lower inputs never paint outside this frame.
                            Layout.preferredHeight: 160
                            Layout.minimumHeight: 160
                            radius: 3
                            color: (themeColor("#2b2b2b", "#fcfcfc", "#1e2c4d", "#f5f9fd"))
                            border.width: 1
                            border.color: (themeColor("#3f3f3f", "#e1e1e1", "#304466", "#dee8f2"))

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 4

                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 20
                                    Label {
                                        text: "ATK 加成"
                                        color: (themeColor("#afafb3", "#50504c", "#b1c0d7", "#5f6f89"))
                                        font.pixelSize: 11
                                        font.weight: Font.DemiBold
                                    }
                                    Label {
                                        text: "武器"
                                        color: (themeColor("#9c9ca1", "#666666", "#8293ae", "#8795aa"))
                                        font.pixelSize: 9
                                    }
                                    Rectangle {
                                        Layout.preferredWidth: 48
                                        Layout.preferredHeight: 24
                                        radius: 3
                                        color: (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff"))
                                        border.width: 1
                                        border.color: permanentWeaponInput.activeFocus ? (themeColor("#707070", "#7a7a7a", "#62bfe8", "#5478b5")) : (themeColor("#4a4a4a", "#d5d5d5", "#3a5077", "#cfdceb"))
                                        TextInput {
                                            id: permanentWeaponInput
                                            anchors.fill: parent
                                            anchors.leftMargin: 6
                                            anchors.rightMargin: 6
                                            text: condBonuses["weapon_passive_permanent"] !== undefined
                                                ? String(condBonuses["weapon_passive_permanent"].value)
                                                : "0"
                                            color: (themeColor("#e1e1e3", "#1b1b1b", "#f3f7fd", "#18223e"))
                                            selectByMouse: true
                                            clip: true
                                            font.pixelSize: 10
                                            verticalAlignment: TextInput.AlignVCenter
                                            onTextEdited: {
                                                condBonuses["weapon_passive_permanent"].value = text
                                                updateEffectiveAtk()
                                            }
                                            onActiveFocusChanged: {
                                                if (!activeFocus)
                                                    commitPermanentBonusValue("weapon_passive_permanent", text)
                                            }
                                        }
                                        MouseArea {
                                            anchors.fill: permanentWeaponInput
                                            acceptedButtons: Qt.NoButton
                                            hoverEnabled: true
                                            cursorShape: Qt.IBeamCursor
                                        }
                                    }
                                    Label {
                                        text: "套装"
                                        color: (themeColor("#9c9ca1", "#666666", "#8293ae", "#8795aa"))
                                        font.pixelSize: 9
                                    }
                                    Rectangle {
                                        Layout.preferredWidth: 48
                                        Layout.preferredHeight: 24
                                        radius: 3
                                        color: (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff"))
                                        border.width: 1
                                        border.color: permanentSetBonusInput.activeFocus ? (themeColor("#707070", "#7a7a7a", "#62bfe8", "#5478b5")) : (themeColor("#4a4a4a", "#d5d5d5", "#3a5077", "#cfdceb"))
                                        TextInput {
                                            id: permanentSetBonusInput
                                            anchors.fill: parent
                                            anchors.leftMargin: 6
                                            anchors.rightMargin: 6
                                            text: condBonuses["set_bonus_permanent"] !== undefined
                                                ? String(condBonuses["set_bonus_permanent"].value)
                                                : "0"
                                            color: (themeColor("#e1e1e3", "#1b1b1b", "#f3f7fd", "#18223e"))
                                            selectByMouse: true
                                            clip: true
                                            font.pixelSize: 10
                                            verticalAlignment: TextInput.AlignVCenter
                                            onTextEdited: {
                                                condBonuses["set_bonus_permanent"].value = text
                                                updateEffectiveAtk()
                                            }
                                            onActiveFocusChanged: {
                                                if (!activeFocus)
                                                    commitPermanentBonusValue("set_bonus_permanent", text)
                                            }
                                        }
                                        MouseArea {
                                            anchors.fill: permanentSetBonusInput
                                            acceptedButtons: Qt.NoButton
                                            hoverEnabled: true
                                            cursorShape: Qt.IBeamCursor
                                        }
                                    }
                                    Item { Layout.fillWidth: true }
                                    Label {
                                        text: effectiveAtkValid
                                            ? "有效 ATK: " + formatNumber(effectiveAtkValue, 5)
                                            : "有效 ATK: —"
                                        color: effectiveAtkValid ? (themeColor("#ff8f86", "#e28a7e", "#ff9a91", "#e77e78")) : (themeColor("#ffaaa0", "#e7a79a", "#ff9a91", "#e77e78"))
                                        font.pixelSize: 12
                                        font.weight: Font.DemiBold
                                    }
                                }

                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: 2
                                    columnSpacing: 8
                                    rowSpacing: 4

                                    Repeater {
                                        model: conditionDefinitions

                                        delegate: RowLayout {
                                            required property var modelData
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 30
                                            spacing: 4

                                            AppCheckBox {
                                                id: conditionToggle
                                                Layout.fillWidth: true
                                                text: modelData.label
                                                checked: condBonuses[modelData.key] !== undefined
                                                    && condBonuses[modelData.key].enabled
                                                font.pixelSize: 10
                                                onToggled: setConditionEnabled(modelData.key, checked)
                                            }

                                            Rectangle {
                                                Layout.preferredWidth: 68
                                                Layout.preferredHeight: 27
                                                radius: 3
                                                color: (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff"))
                                                border.width: 1
                                                border.color: conditionInput.activeFocus ? (themeColor("#707070", "#7a7a7a", "#62bfe8", "#5478b5")) : (themeColor("#4a4a4a", "#d5d5d5", "#3a5077", "#cfdceb"))
                                                opacity: conditionToggle.checked ? 1 : 0.72

                                                TextInput {
                                                    id: conditionInput
                                                    objectName: "conditionInput_" + modelData.key
                                                    anchors.fill: parent
                                                    anchors.leftMargin: 7
                                                    anchors.rightMargin: 7
                                                    text: condBonuses[modelData.key] !== undefined
                                                        ? String(condBonuses[modelData.key].value)
                                                        : "0"
                                                    color: (themeColor("#e1e1e3", "#1b1b1b", "#f3f7fd", "#18223e"))
                                                    selectByMouse: true
                                                    clip: true
                                                    font.pixelSize: 11
                                                    verticalAlignment: TextInput.AlignVCenter
                                                    onTextEdited: {
                                                        condBonuses[modelData.key].value = text
                                                        updateEffectiveAtk()
                                                    }
                                                    onActiveFocusChanged: {
                                                        if (!activeFocus)
                                                            commitConditionValue(modelData.key, text)
                                                    }
                                                }

                                                MouseArea {
                                                    anchors.fill: conditionInput
                                                    acceptedButtons: Qt.NoButton
                                                    hoverEnabled: true
                                                    cursorShape: Qt.IBeamCursor
                                                }
                                            }
                                        }
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 28
                                    spacing: 7

                                    Label {
                                        text: "白值"
                                        color: (themeColor("#d3d3d6", "#2c2c29", "#b1c0d7", "#5f6f89"))
                                        font.pixelSize: 10
                                    }
                                    Rectangle {
                                        Layout.preferredWidth: 86
                                        Layout.preferredHeight: 27
                                        radius: 3
                                        color: ugcImportedFieldsLocked ? (themeColor("#303030", "#f2f2f2", "#1e2c4d", "#edf3f9")) : (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff"))
                                        border.width: 1
                                        border.color: ugcImportedFieldsLocked
                                            ? (themeColor("#3a3a3a", "#ddddda", "#304466", "#d7e3ef"))
                                            : (baseAtkInput.activeFocus ? (themeColor("#707070", "#7a7a7a", "#62bfe8", "#5478b5")) : (themeColor("#4a4a4a", "#d5d5d5", "#3a5077", "#cfdceb")))

                                        TextInput {
                                            id: baseAtkInput
                                            objectName: "baseAtkInput"
                                            anchors.fill: parent
                                            anchors.leftMargin: 7
                                            anchors.rightMargin: 7
                                            text: values["base_atk_input"] !== undefined
                                                ? String(values["base_atk_input"])
                                                : ""
                                            enabled: !ugcImportedFieldsLocked
                                            opacity: ugcImportedFieldsLocked ? 0.52 : 1
                                            color: (themeColor("#e1e1e3", "#1b1b1b", "#f3f7fd", "#18223e"))
                                            selectByMouse: !ugcImportedFieldsLocked
                                            clip: true
                                            font.pixelSize: 11
                                            verticalAlignment: TextInput.AlignVCenter
                                            onTextEdited: {
                                                values["base_atk_input"] = text
                                                updateEffectiveAtk()
                                            }
                                            onActiveFocusChanged: {
                                                if (!activeFocus)
                                                    commitInputValue("base_atk_input", text)
                                            }
                                        }

                                        MouseArea {
                                            anchors.fill: baseAtkInput
                                            acceptedButtons: Qt.NoButton
                                            hoverEnabled: true
                                            cursorShape: Qt.IBeamCursor
                                        }
                                    }
                                    Label {
                                        text: "角色基础 + 武器基础"
                                        color: (themeColor("#86868c", "#797973", "#8293ae", "#8795aa"))
                                        font.pixelSize: 9
                                    }
                                    Item { Layout.fillWidth: true }
                                    Label {
                                        text: "条件 "
                                            + formatNumber(conditionalPercentValue * 100, 5) + "%"
                                            + (conditionalFlatValue !== 0
                                                ? "  +" + formatNumber(conditionalFlatValue, 5)
                                                : "")
                                        color: (themeColor("#9c9ca1", "#666666", "#8293ae", "#8795aa"))
                                        font.pixelSize: 9
                                    }
                                }
                            }
                        }

                        Item { Layout.fillHeight: true }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 3
                    color: (themeColor("#252525", "#ffffff", "#192543", "#ffffff"))
                    border.width: 1
                    border.color: (themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2"))

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 22
                        spacing: 14

                        RowLayout {
                            Layout.fillWidth: true

                            ColumnLayout {
                                spacing: 3
                                Label {
                                    id: modeResultLabel
                                    text: critDamageOnly ? "暴击伤害" : "期望伤害"
                                    transform: Translate { id: modeResultTranslate }
                                    font.pixelSize: 15
                                    color: (themeColor("#e2e2e4", "#1d1d1b", "#f3f7fd", "#18223e"))
                                }
                                Label {
                                    text: "SIGNAL OUTPUT"
                                    font.pixelSize: 11
                                    color: (themeColor("#909095", "#616161", "#8293ae", "#5f6f89"))
                                }
                            }
                            Item { Layout.fillWidth: true }
                            AppButton {
                                id: calculateDamageButton
                                Layout.preferredWidth: 132
                                Layout.preferredHeight: 46
                                onClicked: calculateDamage()
                                contentItem: Text {
                                    anchors.fill: parent
                                    anchors.margins: 4
                                    text: "计算"
                                    color: (themeColor("#f5f5f5", "#ffffff", "#ffffff", "#ffffff"))
                                    font.pixelSize: 14
                                    font.weight: Font.DemiBold
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    radius: 3
                                    color: calculateDamageButton.down
                                        ? (themeColor("#606060", "#454545", "#5b7ed0", "#263a77"))
                                        : (calculateDamageButton.hovered ? (themeColor("#555555", "#3b3b3b", "#4d6fc3", "#3d5caa")) : (themeColor("#4a4a4a", "#323232", "#3d5caa", "#30488f")))
                                    border.width: 1
                                    border.color: calculateDamageButton.hovered ? (themeColor("#787878", "#444444", "#6a89ba", "#3d5caa")) : (themeColor("#686868", "#2a2a2a", "#5874a3", "#263a77"))
                                    Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                                    Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: resultVisible ? 156 : 86
                            radius: 3
                            color: resultVisible ? (themeColor("#252525", "#ffffff", "#192543", "#ffffff")) : (themeColor("#252525", "#ffffff", "#192543", "#ffffff"))
                            border.width: 1
                            border.color: resultVisible ? (themeColor("#686868", "#303030", "#62bfe8", "#30488f")) : (themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2"))

                            Behavior on Layout.preferredHeight {
                                NumberAnimation { duration: 230; easing.type: Easing.OutCubic }
                            }
                            Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 180 } }
                            Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 180 } }

                            Column {
                                anchors.fill: parent
                                anchors.margins: 18
                                spacing: 4

                                Label {
                                    text: lastError !== "" ? "输入错误" : "最终伤害"
                                    color: lastError !== "" ? (themeColor("#ffaaa0", "#e7a79a", "#ff9a91", "#e77e78")) : (themeColor("#dddddf", "#222220", "#dbe5f3", "#24304a"))
                                    font.pixelSize: 12
                                }
                                Label {
                                    text: lastError !== "" ? lastError : (resultVisible ? displayedExpectedDamageText : "等待计算")
                                    color: (themeColor("#dfdfe1", "#20201e", "#f3f7fd", "#18223e"))
                                    font.pixelSize: resultVisible ? 31 : 20
                                    font.weight: Font.DemiBold
                                    font.family: "Consolas"
                                }
                                Label {
                                    visible: resultVisible && lastError === ""
                                    opacity: visible ? 1 : 0
                                    text: "基础区 × 双爆区 × 抗性区 × 擢升区"
                                    color: (themeColor("#9a9a9f", "#666666", "#8293ae", "#8795aa"))
                                    font.pixelSize: 11
                                    Behavior on opacity { NumberAnimation { duration: 180 } }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            radius: 3
                            color: (themeColor("#252525", "#ffffff", "#192543", "#ffffff"))
                            border.width: 1
                            border.color: (themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2"))

                            ScrollView {
                                anchors.fill: parent
                                anchors.margins: 14
                                clip: true

                                Column {
                                    width: parent.width
                                    spacing: 9

                                    Label {
                                        text: "FORMULA CHANNELS"
                                        color: (themeColor("#bcbcc0", "#43433f", "#b1c0d7", "#5f6f89"))
                                        font.pixelSize: 12
                                    }

                                    Repeater {
                                        model: [
                                            ["有效 ATK", "atk"],
                                            ["倍率区", "multiplier_area"],
                                            ["精通提升", "elemental_mastery_bonus"],
                                            ["增伤区", "damage_bonus_area"],
                                            ["加伤区", "additive_area"],
                                            ["基础区", "base_area"],
                                            ["双爆区", "crit_area"],
                                            ["抗性区", "resistance_area"],
                                            ["擢升区", "elevation_area"]
                                        ]
                                        delegate: RowLayout {
                                            required property var modelData
                                            width: parent.width
                                            Label {
                                                text: modelData[0]
                                                color: (themeColor("#9f9fa4", "#60605b", "#8293ae", "#62718c"))
                                                font.pixelSize: 12
                                            }
                                            Item { Layout.fillWidth: true }
                                            Label {
                                                text: resultVisible && coefficients[modelData[1]] !== undefined
                                                    ? formatNumber(coefficients[modelData[1]], 5)
                                                    : "—"
                                                color: (themeColor("#e7e7e8", "#1b1b1b", "#f3f7fd", "#18223e"))
                                                font.pixelSize: 12
                                                font.family: "Consolas"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    SequentialAnimation {
        id: themeTransitionAnimation
        ScriptAction {
            script: {
                themeTransitionRunning = true
                themeTransitionOverlay.opacity = 0
                themeTransitionOverlay.visible = true
            }
        }
        NumberAnimation {
            target: themeTransitionOverlay
            property: "opacity"
            from: 0
            to: 0.28
            duration: 85
            easing.type: Easing.OutQuad
        }
        ScriptAction {
            script: {
                if (pendingThemeAction === 2)
                    furinaTheme = !furinaTheme
                else
                    darkMode = pendingDarkModeValue
                pendingThemeAction = 0
                saveGlobalThemeSettings()
            }
        }
        PauseAnimation { duration: 16 }
        NumberAnimation {
            target: themeTransitionOverlay
            property: "opacity"
            from: 0.28
            to: 0
            duration: 190
            easing.type: Easing.OutCubic
        }
        ScriptAction {
            script: {
                themeTransitionOverlay.visible = false
                themeTransitionRunning = false
            }
        }
    }

    Popup {
        id: themeTransitionOverlay
        parent: Overlay.overlay
        x: 0
        y: 0
        width: parent ? parent.width : window.width
        height: parent ? parent.height : window.height
        z: 100000
        visible: false
        opacity: 0
        modal: true
        dim: false
        padding: 0
        closePolicy: Popup.NoAutoClose
        enter: Transition {}
        exit: Transition {}

        background: Rectangle { color: themeTransitionColor }
        contentItem: Item {}
    }

    Connections {
        target: calculatorBridge
        function onSystemThemeChanged(isDark) {
            if (followSystemTheme)
                setDarkModeAnimated(isDark)
        }
        function onUgcRecognitionFinished(payload) {
            finishUgcRecognition(payload)
        }
        function onUgcWindowCaptureFinished(payload) {
            finishUgcWindowCapture(payload)
        }
    }

    Popup {
        id: ugcLoadingOverlay
        parent: Overlay.overlay
        x: 0
        y: 0
        width: parent ? parent.width : window.width
        height: parent ? parent.height : window.height
        visible: ugcRecognitionBusy
        modal: true
        dim: false
        closePolicy: Popup.NoAutoClose
        padding: 0

        background: Rectangle {
            color: (themeColor("#f2000000", "#f2ffffff", "#f20f1529", "#f2f8fbff"))
            border.width: 0
        }

        contentItem: Item {
            ColumnLayout {
                anchors.centerIn: parent
                spacing: 14

                BusyIndicator {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: 48
                    Layout.preferredHeight: 48
                    running: ugcRecognitionBusy
                    palette.dark: (themeColor("#e8e8e8", "#171717", "#f3f7fd", "#18223e"))
                    palette.highlight: (themeColor("#e8e8e8", "#171717", "#f3f7fd", "#18223e"))
                }
                Label {
                    Layout.alignment: Qt.AlignHCenter
                    text: "正在识别截图"
                    color: (themeColor("#e8e8e8", "#171717", "#f3f7fd", "#18223e"))
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                }
                Label {
                    Layout.alignment: Qt.AlignHCenter
                    text: "正在校准安全区并读取四组角色数据，请稍候…"
                    color: (themeColor("#909095", "#616161", "#8293ae", "#5f6f89"))
                    font.pixelSize: 11
                }
            }
        }
    }

    FileDialog {
        id: ugcScreenshotFileDialog
        title: "选择 UGC 角色面板截图"
        nameFilters: ["图片文件 (*.png *.jpg *.jpeg *.bmp)", "所有文件 (*)"]
        onAccepted: recognizeUgcScreenshot(selectedFile.toString())
    }

    Dialog {
        id: ugcCaptureModeDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 420
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        padding: 20
        Overlay.modal: Rectangle {
            color: darkMode ? "#80000000" : "#66000000"
        }
        background: Rectangle {
            radius: 3
            color: themeColor("#252525", "#ffffff", "#192543", "#ffffff")
            border.width: 1
            border.color: themeColor("#4a4a4a", "#d8d8d8", "#3a5077", "#d5e0ec")
        }
        contentItem: ColumnLayout {
            spacing: 14

            Label {
                Layout.fillWidth: true
                text: "选择截图方式"
                color: themeColor("#f1f1f1", "#1b1b1b", "#f3f7fd", "#18223e")
                font.pixelSize: 16
                font.weight: Font.DemiBold
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2")
            }

            AppButton {
                Layout.fillWidth: true
                Layout.preferredHeight: 44
                text: "点击游戏窗口"
                onClicked: startUgcWindowCapture()
            }

            AppButton {
                Layout.fillWidth: true
                Layout.preferredHeight: 44
                text: "选择截图文件"
                onClicked: {
                    ugcCaptureModeDialog.close()
                    ugcScreenshotFileDialog.open()
                }
            }

            Label {
                Layout.fillWidth: true
                text: "窗口模式支持左键选择，右键或 Esc 取消"
                color: themeColor("#909095", "#616161", "#8293ae", "#5f6f89")
                font.pixelSize: 10
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }

    Dialog {
        id: ugcErrorDialog
        parent: Overlay.overlay
        Overlay.modal: Rectangle {
            color: darkMode ? "#80000000" : "#66000000"
        }
        anchors.centerIn: parent
        width: Math.min(window.width - 80, 520)
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle {
            radius: 3
            color: (themeColor("#252525", "#ffffff", "#192543", "#ffffff"))
            border.width: 1
            border.color: (themeColor("#df6b6b", "#9b3c3c", "#e77e78", "#b45252"))
        }
        contentItem: ColumnLayout {
            spacing: 16
            Label {
                Layout.fillWidth: true
                text: "截图识别失败"
                color: (themeColor("#ffaaa0", "#e7a79a", "#ff9a91", "#e77e78"))
                font.pixelSize: 16
                font.weight: Font.DemiBold
            }
            Label {
                Layout.fillWidth: true
                text: ugcRecognitionError
                wrapMode: Text.Wrap
                color: (themeColor("#d6d6d8", "#323232", "#b1c0d7", "#5f6f89"))
                font.pixelSize: 12
            }
            AppButton {
                Layout.alignment: Qt.AlignRight
                Layout.preferredWidth: 92
                Layout.preferredHeight: 36
                text: "关闭"
                onClicked: ugcErrorDialog.close()
            }
        }
    }

    Dialog {
        id: ugcResultDialog
        parent: Overlay.overlay
        Overlay.modal: Rectangle {
            color: darkMode ? "#80000000" : "#66000000"
        }
        anchors.centerIn: parent
        width: Math.min(window.width - 60, 980)
        height: Math.min(window.height - 60, 590)
        modal: true
        closePolicy: Popup.CloseOnEscape
        background: Rectangle {
            radius: 3
            color: (themeColor("#252525", "#ffffff", "#192543", "#ffffff"))
            border.width: 1
            border.color: (themeColor("#555555", "#70706b", "#5874a3", "#91add0"))
        }
        contentItem: ColumnLayout {
            spacing: 14

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    spacing: 2
                    Label {
                        text: "UGC 角色面板识别结果"
                        color: (themeColor("#e1e1e3", "#1b1b1b", "#f3f7fd", "#18223e"))
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                    }
                    Label {
                        text: "已通过四个白色方块校准安全区 · OCR: "
                            + String(ugcRecognitionInfo.ocrBackend || "—")
                        color: (themeColor("#909095", "#616161", "#8293ae", "#5f6f89"))
                        font.pixelSize: 10
                    }
                }
                Item { Layout.fillWidth: true }
                AppButton {
                    Layout.preferredWidth: 78
                    Layout.preferredHeight: 34
                    text: "关闭"
                    onClicked: ugcResultDialog.close()
                }
            }

            GridLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                columns: 4
                columnSpacing: 10

                Repeater {
                    model: ugcCharacters
                    delegate: AppButton {
                        id: ugcCharacterCard
                        required property var modelData
                        required property int index
                        property bool selected: index === ugcSelectedIndex
                        property real cardWidth: selected ? 252 : 215
                        Layout.preferredWidth: cardWidth
                        Layout.fillHeight: true
                        onClicked: ugcSelectedIndex = index

                        Behavior on cardWidth {
                            NumberAnimation { duration: 170; easing.type: Easing.OutCubic }
                        }

                        background: Rectangle {
                            radius: 3
                            color: ugcCharacterCard.selected
                                ? (ugcCharacterCard.hovered ? (themeColor("#3d3d3d", "#f5f5f5", "#4d6fc3", "#d5f2fc")) : (themeColor("#333333", "#f2f2f2", "#3d5caa", "#e1f7fe")))
                                : (ugcCharacterCard.hovered ? (themeColor("#333333", "#f7f7f7", "#2a3d63", "#f4f7fb")) : (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff")))
                            border.width: ugcCharacterCard.selected ? 2 : 1
                            border.color: ugcCharacterCard.selected ? (themeColor("#707070", "#232323", "#55d7fa", "#30488f")) : (themeColor("#383838", "#e1e1e1", "#304466", "#dee8f2"))
                            Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                        }

                        contentItem: Item {
                            clip: true

                            ColumnLayout {
                                id: ugcCardContent
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 8
                                transformOrigin: Item.Center
                                // Keep the selected content at its natural size; shrink idle cards
                                // slightly so selection feels larger without consuming its inner margin.
                                scale: ugcCharacterCard.selected ? 1 : 0.95

                                Behavior on scale {
                                    NumberAnimation { duration: 150; easing.type: Easing.OutCubic }
                                }

                                Label {
                                    text: modelData.name
                                    color: (themeColor("#e1e1e3", "#1b1b1b", "#f3f7fd", "#18223e"))
                                    font.pixelSize: 15
                                    font.weight: Font.DemiBold
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 1
                                    color: (themeColor("#4a4a4a", "#d5d5d5", "#3a5077", "#cfdceb"))
                                }
                                Label { text: "ATK"; color: (themeColor("#909095", "#616161", "#8293ae", "#5f6f89")); font.pixelSize: 10 }
                                Label {
                                    text: modelData.display.atk
                                    color: (themeColor("#e8e8e8", "#171717", "#f3f7fd", "#18223e"))
                                    font.pixelSize: 20
                                    font.weight: Font.DemiBold
                                }
                                Label {
                                    text: "白值  " + modelData.display.basicAtk
                                    color: (themeColor("#b7b7bb", "#505050", "#b1c0d7", "#5f6f89"))
                                    font.pixelSize: 11
                                }
                                Label {
                                    text: "暴击率  " + modelData.display.critRatePercent + "%"
                                    color: (themeColor("#b7b7bb", "#505050", "#b1c0d7", "#5f6f89"))
                                    font.pixelSize: 11
                                }
                                Label {
                                    text: "暴击伤害  " + modelData.display.critDamagePercent + "%"
                                    color: (themeColor("#b7b7bb", "#505050", "#b1c0d7", "#5f6f89"))
                                    font.pixelSize: 11
                                }
                                Item { Layout.fillHeight: true }
                                Label {
                                    Layout.fillWidth: true
                                    text: "原始：" + modelData.raw.atk
                                    color: (themeColor("#88888c", "#777777", "#8293ae", "#8795aa"))
                                    font.pixelSize: 9
                                    elide: Text.ElideRight
                                }
                            }
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: "选择一个角色位置后应用到当前配置槽"
                    color: (themeColor("#909095", "#616161", "#8293ae", "#5f6f89"))
                    font.pixelSize: 11
                }
                Item { Layout.fillWidth: true }
                AppButton {
                    id: applyUgcButton
                    Layout.preferredWidth: 176
                    Layout.preferredHeight: 42
                    text: "应用选中角色"
                    enabled: ugcCharacters.length > ugcSelectedIndex
                    onClicked: applyUgcCharacter(ugcCharacters[ugcSelectedIndex])
                    contentItem: Text {
                        text: applyUgcButton.text
                        color: applyUgcButton.enabled ? (themeColor("#f5f5f5", "#ffffff", "#ffffff", "#ffffff")) : (themeColor("#909090", "#9a9a96", "#66758e", "#aab4c2"))
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: 3
                        color: !applyUgcButton.enabled
                            ? (themeColor("#252525", "#fafafa", "#192543", "#f8fbff"))
                            : (applyUgcButton.down
                                ? (themeColor("#606060", "#454545", "#5b7ed0", "#263a77"))
                                : (applyUgcButton.hovered ? (themeColor("#555555", "#3b3b3b", "#4d6fc3", "#3d5caa")) : (themeColor("#4a4a4a", "#323232", "#3d5caa", "#30488f"))))
                        border.width: 1
                        border.color: applyUgcButton.enabled ? (themeColor("#686868", "#2a2a2a", "#5874a3", "#263a77")) : (themeColor("#383838", "#e5e5e5", "#304466", "#dee8f2"))
                    }
                }
            }
        }
    }

    AtkPage {
        id: atkPage
        darkMode: window.darkMode
        furinaTheme: window.furinaTheme
        themeTransitionRunning: window.themeTransitionRunning
        anchors.fill: parent
        z: currentPage === 1 ? 2 : 1
        enabled: currentPage === 1
        visible: opacity > 0
        opacity: currentPage === 1 ? 1 : 0
        transform: Translate {
            y: currentPage === 1 ? 0 : 52
            Behavior on y { NumberAnimation { duration: 270; easing.type: Easing.OutCubic } }
        }
        Behavior on opacity { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }

        onApplyToDamage: function(atkValue, baseValue) {
            applyAtkResult(atkValue, baseValue)
        }
    }

}

