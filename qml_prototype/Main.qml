import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Material
import QtQuick.Dialogs

ApplicationWindow {
    id: window
    width: 1180
    height: 820
    minimumWidth: 940
    minimumHeight: 760
    visible: true
    title: "原神星超导角色伤害计算器 · QML 原型"

    Material.theme: Material.Dark
    Material.accent: "#5a8dee"
    Material.primary: "#17223b"
    color: "#0d1424"

    property var values: ({})
    property var slots: []
    property int currentSlot: 1
    property string slotName: ""
    property bool critDamageOnly: false
    property bool mainPctMode: false
    property int currentPage: 0
    property int pendingPage: 0
    property bool navigationButtonAtRight: false
    property int pendingSlot: 1
    property int slotDirection: 1
    property bool resultVisible: false
    property string lastError: ""
    property string statusMessage: "正在读取配置槽…"
    property bool autoSaveEnabled: true
    property real expectedDamage: 0
    property var coefficients: ({})
    property var inputGroups: [
        {"title": "角色面板", "keys": ["atk", "em", "crit_rate", "crit_damage"]},
        {"title": "反应参数", "keys": ["talent_multiplier", "stacks", "reaction_bonus", "base_reaction_damage_bonus"]},
        {"title": "目标与附加", "keys": ["flat_damage_increase", "enemy_resistance", "elevation_bonus"]}
    ]
    property var conditionDefinitions: [
        {"key": "weapon_passive", "label": "武器特效 ATK%（不常驻）", "percent": true},
        {"key": "set_bonus", "label": "圣遗物套装 ATK%", "percent": true},
        {"key": "other_pct", "label": "其他 ATK%", "percent": true},
        {"key": "other_flat", "label": "其他固定 ATK", "percent": false}
    ]
    property var condBonuses: defaultConditionalBonuses()
    property var conditionalBonusKeys: [
        "weapon_passive_permanent", "weapon_passive", "set_bonus", "other_pct", "other_flat"
    ]
    property real effectiveAtkValue: 0
    property bool effectiveAtkValid: true
    property real conditionalPercentValue: 0
    property real conditionalFlatValue: 0
    property var ugcCharacters: []
    property int ugcSelectedIndex: 0
    property var ugcRecognitionInfo: ({})
    property string ugcRecognitionError: ""

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

    function commitPermanentWeaponValue(value) {
        const next = normalizeConditionalBonuses(condBonuses)
        next["weapon_passive_permanent"].value = trimDecimalText(value)
        next["weapon_passive_permanent"].enabled = true
        condBonuses = next
        updateEffectiveAtk()
    }

    function permanentWeaponPercent() {
        const entry = condBonuses["weapon_passive_permanent"]
        const value = Number(entry === undefined ? 0 : (entry.value || 0))
        return mainPctMode ? value / 100.0 : value
    }

    function ugcPanelIncludesPermanentWeapon() {
        return String(values["__ugc_atk_includes_weapon_permanent__"] || "False") === "True"
    }

    function effectiveAtkSummary() {
        const panelAtk = Number(values["atk"] || 0)
        const baseAtk = Number(values["base_atk_input"] || 0)
        const permanentPercent = permanentWeaponPercent()
        if (!isFinite(panelAtk) || !isFinite(baseAtk) || !isFinite(permanentPercent))
            return {"valid": false, "effective": 0, "percent": 0, "flat": 0,
                    "panel": panelAtk, "base": baseAtk}

        let percent = permanentPercent
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
            const importedPermanent = Number(values["__ugc_weapon_permanent_at_import__"] || 0)
            if (!isFinite(importedPermanent))
                return {"valid": false, "effective": 0, "percent": 0, "flat": 0,
                        "panel": panelAtk, "base": baseAtk}
            panelBase -= baseAtk * importedPermanent
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

    function loadSlot(slot) {
        const response = JSON.parse(calculatorBridge.loadSlot(slot))
        if (!response.ok) {
            setStatusMessage(response.error)
            return
        }
        currentSlot = slot
        values = normalizeInputValues(response.values)
        slotName = response.name
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
        const next = ({})
        for (const key in values)
            next[key] = values[key]
        next["atk"] = trimDecimalText(atkValue)
        next["base_atk_input"] = trimDecimalText(baseValue)
        next["__ugc_atk_includes_weapon_permanent__"] = "False"
        next["__ugc_weapon_permanent_at_import__"] = "0"
        values = next
        updateEffectiveAtk()
        if (autoSaveEnabled)
            saveCurrent(false)
        setStatusMessage("已从 ATK 计算器应用角色 ATK")
        showDamagePage()
    }

    function recognizeUgcScreenshot(fileUrl) {
        setStatusMessage("正在识别 UGC 面板截图…")
        const response = JSON.parse(calculatorBridge.recognizeUgcScreenshot(String(fileUrl)))
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
        const next = ({})
        for (const key in values)
            next[key] = values[key]
        next["atk"] = trimDecimalText(decoded.atk)
        next["base_atk_input"] = trimDecimalText(decoded.basic_atk)
        const displayFactor = mainPctMode ? 100.0 : 1.0
        next["crit_rate"] = formatNumber(Number(decoded.crit_rate) * displayFactor, 10)
        next["crit_damage"] = formatNumber(Number(decoded.crit_damage) * displayFactor, 10)
        const permanentAtImport = permanentWeaponPercent()
        if (!isFinite(permanentAtImport)) {
            setStatusMessage("武器常驻 ATK% 不是有效数字")
            return
        }
        next["__ugc_atk_includes_weapon_permanent__"] = "True"
        next["__ugc_weapon_permanent_at_import__"] = formatNumber(permanentAtImport, 10)
        values = next
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
        const percentConditionKeys = ["weapon_passive_permanent", "weapon_passive", "set_bonus", "other_pct"]
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
        reloadSlotList(true)
    }

    header: ToolBar {
        height: 64
        background: Rectangle { color: "#111b30" }

        Item {
            anchors.fill: parent

            ColumnLayout {
                anchors.left: parent.left
                anchors.leftMargin: 28
                anchors.verticalCenter: parent.verticalCenter
                spacing: 0

                Label {
                    text: "原神星超导角色伤害计算器"
                    font.pixelSize: 19
                    font.weight: Font.DemiBold
                    color: "#eef4ff"
                }
                Label {
                    text: "PySide6 + QML / 使用 CTK 同一套配置槽"
                    font.pixelSize: 11
                    color: "#8fa2c7"
                }
            }

            AppButton {
                id: pageNavigationButton
                width: 122
                height: 36
                anchors.verticalCenter: parent.verticalCenter
                x: parent.width - 24 - width - (navigationButtonAtRight ? 0 : modeBadge.width + 14)
                onClicked: currentPage === 0 ? showAtkPage() : showDamagePage()

                Behavior on x {
                    NumberAnimation { duration: 260; easing.type: Easing.InOutCubic }
                }

                contentItem: Text {
                    id: pageNavigationText
                    anchors.fill: parent
                    text: currentPage === 0 ? "ATK 计算器" : "返回伤害计算"
                    transform: Translate { id: pageNavigationTranslate }
                    color: "#e5eeff"
                    font.pixelSize: 11
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 6
                    color: pageNavigationButton.down
                        ? "#142238"
                        : (pageNavigationButton.hovered ? "#243a5d" : "#1a2943")
                    border.width: 1
                    border.color: pageNavigationButton.hovered ? "#5f7fab" : "#3d567d"
                    Behavior on color { ColorAnimation { duration: 110 } }
                    Behavior on border.color { ColorAnimation { duration: 110 } }
                }
            }

            Rectangle {
                id: modeBadge
                width: 138
                height: 32
                anchors.right: parent.right
                anchors.rightMargin: 24
                anchors.verticalCenter: parent.verticalCenter
                radius: 8
                opacity: currentPage === 0 ? 1 : 0
                visible: opacity > 0
                transform: Translate {
                    y: currentPage === 0 ? 0 : -18
                    Behavior on y { NumberAnimation { duration: 190; easing.type: Easing.InCubic } }
                }
                color: critDamageOnly ? "#384f7a" : "#1c2b47"
                border.width: 1
                border.color: critDamageOnly ? "#80a8ff" : "#32466d"

                Behavior on color { ColorAnimation { duration: 160 } }
                Behavior on opacity { NumberAnimation { duration: 160 } }

                Text {
                    id: modeBadgeText
                    anchors.centerIn: parent
                    text: critDamageOnly ? "暴击伤害模式" : "期望伤害模式"
                    transform: Translate { id: modeBadgeTranslate }
                    color: "#dce8ff"
                    font.pixelSize: 12
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: toggleDamageModeAnimated()
                }
            }
        }
    }

    Rectangle {
        id: damagePage
        anchors.fill: parent
        z: currentPage === 0 ? 2 : 1
        enabled: currentPage === 0
        visible: opacity > 0
        opacity: currentPage === 0 ? 1 : 0
        color: "#0d1424"
        transform: Translate {
            y: currentPage === 0 ? 0 : -48
            Behavior on y { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }
        }
        Behavior on opacity { NumberAnimation { duration: 210; easing.type: Easing.OutCubic } }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 22
            spacing: 12

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 64
                radius: 12
                color: "#121d32"
                border.width: 1
                border.color: "#263958"

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14
                    spacing: 8

                    Label {
                        text: "配置槽"
                        color: "#b9cbed"
                        font.pixelSize: 12
                    }

                    Repeater {
                        model: slots
                        delegate: AppButton {
                            id: slotButton
                            required property var modelData
                            checkable: true
                            checked: modelData.id === currentSlot
                            Layout.preferredHeight: 36
                            Layout.preferredWidth: Math.max(96, Math.min(156, slotText.implicitWidth + 34))
                            onClicked: switchSlot(modelData.id)

                            contentItem: Text {
                                id: slotText
                                anchors.fill: parent
                                anchors.margins: 4
                                text: modelData.name || ("配置 " + modelData.id)
                                color: slotButton.checked ? "#ffffff" : "#cbd9f4"
                                font.pixelSize: 12
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                elide: Text.ElideRight
                            }
                            background: Rectangle {
                                radius: 6
                                color: slotButton.checked
                                    ? (slotButton.hovered ? "#3d6fce" : "#315fbb")
                                    : (slotButton.down
                                        ? "#142238"
                                        : (slotButton.hovered ? "#243a5d" : "#1a2943"))
                                border.width: 1
                                border.color: slotButton.checked
                                    ? (slotButton.hovered ? "#a0bdff" : "#7ea7ff")
                                    : (slotButton.hovered ? "#5f7fab" : "#314665")
                                Behavior on color { ColorAnimation { duration: 120 } }
                                Behavior on border.color { ColorAnimation { duration: 120 } }
                            }
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: 1
                        Layout.preferredHeight: 28
                        color: "#314665"
                    }

                    Label {
                        text: "名称"
                        color: "#8fa2c7"
                        font.pixelSize: 11
                    }

                    TextField {
                        id: slotNameInput
                        Layout.preferredWidth: 145
                        Layout.preferredHeight: 33
                        text: slotName
                        selectByMouse: true
                        placeholderText: ""
                        leftPadding: 10
                        rightPadding: 10
                        color: "#edf4ff"
                        onTextEdited: slotName = text
                        onEditingFinished: {
                            if (autoSaveEnabled)
                                saveCurrent(false)
                        }
                        background: Rectangle {
                            radius: 7
                            color: slotNameInput.activeFocus ? "#192944" : "#101a2d"
                            border.width: 1
                            border.color: slotNameInput.activeFocus ? "#608fed" : "#314665"
                            Behavior on color { ColorAnimation { duration: 120 } }
                            Behavior on border.color { ColorAnimation { duration: 120 } }
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
                            color: "#ffffff"
                            font.pixelSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            radius: 8
                            color: slotSaveButton.down
                                ? "#3f70c8"
                                : (slotSaveButton.hovered ? "#6b9bf2" : "#5a8dee")
                            border.width: 1
                            border.color: slotSaveButton.hovered ? "#91b5ff" : "#6f9df0"
                            Behavior on color { ColorAnimation { duration: 110 } }
                            Behavior on border.color { ColorAnimation { duration: 110 } }
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
                        color: "#8196bd"
                        font.pixelSize: 11
                        Layout.preferredWidth: visible ? 132 : 0
                        Layout.maximumWidth: 132
                        Layout.minimumWidth: 0
                        elide: Text.ElideRight
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
                    radius: 14
                    color: "#121d32"
                    border.width: 1
                    border.color: "#263958"

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
                                color: "#ecf3ff"
                            }
                            Item { Layout.fillWidth: true }
                            AppButton {
                                id: ugcImportButton
                                Layout.preferredWidth: 94
                                Layout.preferredHeight: 34
                                onClicked: ugcScreenshotFileDialog.open()
                                contentItem: Text {
                                    anchors.fill: parent
                                    text: "截图识别"
                                    color: "#dce8ff"
                                    font.pixelSize: 11
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    radius: 6
                                    color: ugcImportButton.down
                                        ? "#203552"
                                        : (ugcImportButton.hovered ? "#304d79" : "#263b60")
                                    border.width: 1
                                    border.color: ugcImportButton.hovered ? "#6388bd" : "#46658f"
                                    Behavior on color { ColorAnimation { duration: 110 } }
                                    Behavior on border.color { ColorAnimation { duration: 110 } }
                                }
                            }
                            AppButton {
                                id: mainInputModeButton
                                Layout.preferredWidth: 104
                                Layout.preferredHeight: 34
                                onClicked: toggleInputModeAnimated()
                                contentItem: Text {
                                    id: inputModeButtonText
                                    anchors.fill: parent
                                    anchors.margins: 4
                                    text: mainPctMode === true ? "百分数输入" : "小数输入"
                                    transform: Translate { id: inputModeButtonTranslate }
                                    color: "#e3ecff"
                                    font.pixelSize: 11
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    radius: 6
                                    color: mainInputModeButton.down
                                        ? "#203552"
                                        : (mainInputModeButton.hovered ? "#304d79" : "#263b60")
                                    border.width: 1
                                    border.color: mainInputModeButton.hovered ? "#6388bd" : "#46658f"
                                    Behavior on color { ColorAnimation { duration: 110 } }
                                    Behavior on border.color { ColorAnimation { duration: 110 } }
                                }
                            }
                        }

                        Label {
                            id: inputModeHintText
                            text: mainPctMode ? "百分比使用 70 这样的数字输入" : "百分比使用 0.7 这样的数字输入"
                            transform: Translate { id: inputModeHintTranslate }
                            font.pixelSize: 11
                            color: "#8196bd"
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
                                        color: "#9eb4dd"
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
                                                required property string modelData
                                                property var fieldData: window.fieldDefinition(modelData)
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: 50
                                                radius: 9
                                                color: input.activeFocus ? "#192944" : "#101a2d"
                                                border.width: 1
                                                border.color: input.activeFocus ? "#608fed" : "#263958"

                                                Behavior on color { ColorAnimation { duration: 120 } }
                                                Behavior on border.color { ColorAnimation { duration: 120 } }

                                                Label {
                                                    anchors.left: parent.left
                                                    anchors.top: parent.top
                                                    anchors.leftMargin: 10
                                                    anchors.topMargin: 5
                                                    text: fieldData.label
                                                    font.pixelSize: 11
                                                    color: "#dbe8ff"
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
                                                    color: "#7f93b9"
                                                }

                                                TextInput {
                                                    id: input
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
                                                    selectByMouse: true
                                                    clip: true
                                                    color: "#f0f5ff"
                                                    selectionColor: "#4f7ed5"
                                                    selectedTextColor: "#ffffff"
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
                            Layout.preferredHeight: 146
                            Layout.minimumHeight: 146
                            radius: 9
                            color: "#101a2d"
                            border.width: 1
                            border.color: "#2d4263"

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 4

                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 20
                                    Label {
                                        text: "攻击力加成 & 白值"
                                        color: "#a9bfe7"
                                        font.pixelSize: 11
                                        font.weight: Font.DemiBold
                                    }
                                    Label {
                                        text: "武器常驻 ATK%"
                                        color: "#8fa7cf"
                                        font.pixelSize: 9
                                    }
                                    Rectangle {
                                        Layout.preferredWidth: 58
                                        Layout.preferredHeight: 24
                                        radius: 5
                                        color: "#0d1729"
                                        border.width: 1
                                        border.color: permanentWeaponInput.activeFocus ? "#608fed" : "#304665"
                                        TextInput {
                                            id: permanentWeaponInput
                                            anchors.fill: parent
                                            anchors.leftMargin: 6
                                            anchors.rightMargin: 6
                                            text: condBonuses["weapon_passive_permanent"] !== undefined
                                                ? String(condBonuses["weapon_passive_permanent"].value)
                                                : "0"
                                            color: "#edf4ff"
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
                                                    commitPermanentWeaponValue(text)
                                            }
                                        }
                                        MouseArea {
                                            anchors.fill: permanentWeaponInput
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
                                        color: effectiveAtkValid ? "#ff7272" : "#ff9f9f"
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
                                                radius: 5
                                                color: "#0d1729"
                                                border.width: 1
                                                border.color: conditionInput.activeFocus ? "#608fed" : "#304665"
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
                                                    color: "#edf4ff"
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
                                        color: "#dbe8ff"
                                        font.pixelSize: 10
                                    }
                                    Rectangle {
                                        Layout.preferredWidth: 86
                                        Layout.preferredHeight: 27
                                        radius: 5
                                        color: "#0d1729"
                                        border.width: 1
                                        border.color: baseAtkInput.activeFocus ? "#608fed" : "#304665"

                                        TextInput {
                                            id: baseAtkInput
                                            objectName: "baseAtkInput"
                                            anchors.fill: parent
                                            anchors.leftMargin: 7
                                            anchors.rightMargin: 7
                                            text: values["base_atk_input"] !== undefined
                                                ? String(values["base_atk_input"])
                                                : ""
                                            color: "#edf4ff"
                                            selectByMouse: true
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
                                        color: "#6f86ad"
                                        font.pixelSize: 9
                                    }
                                    Item { Layout.fillWidth: true }
                                    Label {
                                        text: "条件 "
                                            + formatNumber(conditionalPercentValue * 100, 5) + "%"
                                            + (conditionalFlatValue !== 0
                                                ? "  +" + formatNumber(conditionalFlatValue, 5)
                                                : "")
                                        color: "#8fa7cf"
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
                    radius: 14
                    color: "#121d32"
                    border.width: 1
                    border.color: "#263958"

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
                                    color: "#9ebeff"
                                }
                                Label {
                                    text: "核心公式结果"
                                    font.pixelSize: 11
                                    color: "#8196bd"
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
                                    color: "#ffffff"
                                    font.pixelSize: 14
                                    font.weight: Font.DemiBold
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    radius: 8
                                    color: calculateDamageButton.down
                                        ? "#3f70c8"
                                        : (calculateDamageButton.hovered ? "#6b9bf2" : "#5a8dee")
                                    border.width: 1
                                    border.color: calculateDamageButton.hovered ? "#91b5ff" : "#6f9df0"
                                    Behavior on color { ColorAnimation { duration: 110 } }
                                    Behavior on border.color { ColorAnimation { duration: 110 } }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: resultVisible ? 156 : 86
                            radius: 12
                            color: resultVisible ? "#172845" : "#101a2d"
                            border.width: 1
                            border.color: resultVisible ? "#4c78cb" : "#263958"

                            Behavior on Layout.preferredHeight {
                                NumberAnimation { duration: 230; easing.type: Easing.OutCubic }
                            }
                            Behavior on color { ColorAnimation { duration: 180 } }
                            Behavior on border.color { ColorAnimation { duration: 180 } }

                            Column {
                                anchors.fill: parent
                                anchors.margins: 18
                                spacing: 4

                                Label {
                                    text: lastError !== "" ? "输入错误" : "最终伤害"
                                    color: lastError !== "" ? "#ff9f9f" : "#96baff"
                                    font.pixelSize: 12
                                }
                                Label {
                                    text: lastError !== "" ? lastError : (resultVisible ? formatNumber(expectedDamage, 5) : "等待计算")
                                    color: "#f3f7ff"
                                    font.pixelSize: resultVisible ? 31 : 20
                                    font.weight: Font.DemiBold
                                    Behavior on font.pixelSize { NumberAnimation { duration: 180 } }
                                }
                                Label {
                                    visible: resultVisible && lastError === ""
                                    opacity: visible ? 1 : 0
                                    text: "基础区 × 双爆区 × 抗性区 × 擢升区"
                                    color: "#8da1c6"
                                    font.pixelSize: 11
                                    Behavior on opacity { NumberAnimation { duration: 180 } }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            radius: 12
                            color: "#101a2d"
                            border.width: 1
                            border.color: "#263958"

                            ScrollView {
                                anchors.fill: parent
                                anchors.margins: 14
                                clip: true

                                Column {
                                    width: parent.width
                                    spacing: 9

                                    Label {
                                        text: "计算分区"
                                        color: "#bdcff1"
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
                                                color: "#90a6cf"
                                                font.pixelSize: 12
                                            }
                                            Item { Layout.fillWidth: true }
                                            Label {
                                                text: resultVisible && coefficients[modelData[1]] !== undefined
                                                    ? formatNumber(coefficients[modelData[1]], 5)
                                                    : "—"
                                                color: "#e5eeff"
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

    FileDialog {
        id: ugcScreenshotFileDialog
        title: "选择 UGC 角色面板截图"
        nameFilters: ["图片文件 (*.png *.jpg *.jpeg *.bmp)", "所有文件 (*)"]
        onAccepted: recognizeUgcScreenshot(selectedFile.toString())
    }

    Dialog {
        id: ugcErrorDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(window.width - 80, 520)
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle {
            radius: 12
            color: "#121d32"
            border.width: 1
            border.color: "#6e4050"
        }
        contentItem: ColumnLayout {
            spacing: 16
            Label {
                Layout.fillWidth: true
                text: "截图识别失败"
                color: "#ff9f9f"
                font.pixelSize: 16
                font.weight: Font.DemiBold
            }
            Label {
                Layout.fillWidth: true
                text: ugcRecognitionError
                wrapMode: Text.Wrap
                color: "#dce8ff"
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
        anchors.centerIn: parent
        width: Math.min(window.width - 60, 980)
        height: Math.min(window.height - 60, 590)
        modal: true
        closePolicy: Popup.CloseOnEscape
        background: Rectangle {
            radius: 14
            color: "#0f192c"
            border.width: 1
            border.color: "#41628e"
        }
        contentItem: ColumnLayout {
            spacing: 14

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    spacing: 2
                    Label {
                        text: "UGC 角色面板识别结果"
                        color: "#edf4ff"
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                    }
                    Label {
                        text: "已通过四个白色方块校准安全区 · OCR: "
                            + String(ugcRecognitionInfo.ocrBackend || "—")
                        color: "#8196bd"
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
                        checkable: true
                        checked: index === ugcSelectedIndex
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        onClicked: ugcSelectedIndex = index

                        background: Rectangle {
                            radius: 11
                            color: ugcCharacterCard.checked
                                ? (ugcCharacterCard.hovered ? "#203b66" : "#192f51")
                                : (ugcCharacterCard.hovered ? "#172741" : "#111c30")
                            border.width: ugcCharacterCard.checked ? 2 : 1
                            border.color: ugcCharacterCard.checked ? "#6f9ff3" : "#2b405f"
                            Behavior on color { ColorAnimation { duration: 110 } }
                        }

                        contentItem: ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8
                            Label {
                                text: modelData.name
                                color: "#edf4ff"
                                font.pixelSize: 15
                                font.weight: Font.DemiBold
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 1
                                color: "#314665"
                            }
                            Label { text: "ATK"; color: "#8196bd"; font.pixelSize: 10 }
                            Label {
                                text: modelData.display.atk
                                color: "#ffffff"
                                font.pixelSize: 20
                                font.weight: Font.DemiBold
                            }
                            Label {
                                text: "白值  " + modelData.display.basicAtk
                                color: "#b9cbed"
                                font.pixelSize: 11
                            }
                            Label {
                                text: "暴击率  " + modelData.display.critRatePercent + "%"
                                color: "#b9cbed"
                                font.pixelSize: 11
                            }
                            Label {
                                text: "暴击伤害  " + modelData.display.critDamagePercent + "%"
                                color: "#b9cbed"
                                font.pixelSize: 11
                            }
                            Item { Layout.fillHeight: true }
                            Label {
                                Layout.fillWidth: true
                                text: "原始：" + modelData.raw.atk
                                color: "#657ca4"
                                font.pixelSize: 9
                                elide: Text.ElideRight
                            }
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: "选择一个角色位置后应用到当前配置槽"
                    color: "#8196bd"
                    font.pixelSize: 11
                }
                Item { Layout.fillWidth: true }
                AppButton {
                    Layout.preferredWidth: 112
                    Layout.preferredHeight: 40
                    text: "取消"
                    onClicked: ugcResultDialog.close()
                }
                AppButton {
                    id: applyUgcButton
                    Layout.preferredWidth: 176
                    Layout.preferredHeight: 42
                    text: "应用选中角色"
                    enabled: ugcCharacters.length > ugcSelectedIndex
                    onClicked: applyUgcCharacter(ugcCharacters[ugcSelectedIndex])
                    background: Rectangle {
                        radius: 8
                        color: !applyUgcButton.enabled
                            ? "#202b3e"
                            : (applyUgcButton.down
                                ? "#34775f"
                                : (applyUgcButton.hovered ? "#55b88e" : "#47a982"))
                        border.width: 1
                        border.color: applyUgcButton.enabled ? "#6acfa3" : "#2c3950"
                    }
                }
            }
        }
    }

    AtkPage {
        id: atkPage
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

