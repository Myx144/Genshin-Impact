import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    signal applyToDamage(string atkValue, string baseValue)

    property bool darkMode: false
    property bool furinaTheme: false
    property bool themeTransitionRunning: false
    property bool percentMode: false
    property var config: ({})
    property bool resultVisible: false
    property string errorText: ""
    property string statusText: "正在读取 ATK 配置…"
    property var result: ({})
    property var artifacts: [
        {"key": "flower", "name": "生之花", "fields": ["sub_flat", "sub_pct"]},
        {"key": "plume", "name": "死之羽", "fields": ["main_flat", "sub_pct"]},
        {"key": "sands", "name": "时之沙", "fields": ["main_pct", "sub_flat", "sub_pct"]},
        {"key": "goblet", "name": "空之杯", "fields": ["main_pct", "sub_flat", "sub_pct"]},
        {"key": "circlet", "name": "理之冠", "fields": ["main_pct", "sub_flat", "sub_pct"]}
    ]

    function themeColor(defaultDark, defaultLight, furinaDark, furinaLight) {
        return furinaTheme
            ? (darkMode ? furinaDark : furinaLight)
            : (darkMode ? defaultDark : defaultLight)
    }

    function fieldLabel(field) {
        const labels = {
            "main_flat": "主词条固定 ATK",
            "main_pct": "主词条 ATK%",
            "sub_flat": "副词条固定 ATK",
            "sub_pct": "副词条 ATK%"
        }
        return labels[field] || field
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

    function loadConfig() {
        const response = JSON.parse(calculatorBridge.loadAtkConfig())
        if (!response.ok) {
            statusText = response.error
            return
        }
        config = response.config
        statusText = "已读取 ATK 配置"
    }

    function saveConfig(showMessage) {
        const response = JSON.parse(calculatorBridge.saveAtkConfig(JSON.stringify(config)))
        if (!response.ok) {
            statusText = response.error
            return false
        }
        if (showMessage)
            statusText = "ATK 配置已保存"
        return true
    }

    function calculateAtk() {
        errorText = ""
        const response = JSON.parse(calculatorBridge.calculateAtk(JSON.stringify(config), percentMode))
        if (!response.ok) {
            errorText = response.error
            resultVisible = false
            return
        }
        result = response
        resultVisible = true
        saveConfig(false)
    }

    function applyResult() {
        if (!resultVisible) {
            calculateAtk()
            if (!resultVisible)
                return
        }
        applyToDamage(formatNumber(result.finalAtk, 5), formatNumber(result.baseAtk, 5))
    }

    function togglePercentModeAnimated() {
        if (!percentModeTextAnimation.running)
            percentModeTextAnimation.start()
    }

    function togglePercentMode() {
        const factor = percentMode ? 0.01 : 100.0
        const next = JSON.parse(JSON.stringify(config))
        next.weapon_secondary = formatNumber(Number(next.weapon_secondary || 0) * factor, 10)
        for (let artifactIndex = 0; artifactIndex < artifacts.length; artifactIndex++) {
            const artifact = artifacts[artifactIndex]
            for (let fieldIndex = 0; fieldIndex < artifact.fields.length; fieldIndex++) {
                const field = artifact.fields[fieldIndex]
                if (field.indexOf("pct") !== -1) {
                    next[artifact.key][field].value = formatNumber(
                        Number(next[artifact.key][field].value || 0) * factor,
                        10
                    )
                }
            }
        }
        config = next
        percentMode = !percentMode
    }

    function fillMaxedMainStats() {
        const next = JSON.parse(JSON.stringify(config))
        next.plume.main_flat.checked = true
        next.plume.main_flat.value = "311"
        for (const key of ["sands", "goblet", "circlet"]) {
            next[key].main_pct.checked = true
            next[key].main_pct.value = percentMode ? "46.6" : "0.466"
        }
        config = next
    }

    SequentialAnimation {
        id: percentModeTextAnimation
        ParallelAnimation {
            NumberAnimation { target: percentModeButtonText; property: "opacity"; to: 0; duration: 90 }
            NumberAnimation { target: percentModeButtonTranslate; property: "y"; to: -7; duration: 105; easing.type: Easing.InCubic }
        }
        ScriptAction {
            script: {
                togglePercentMode()
                percentModeButtonTranslate.y = 7
            }
        }
        ParallelAnimation {
            NumberAnimation { target: percentModeButtonText; property: "opacity"; to: 1; duration: 130 }
            NumberAnimation { target: percentModeButtonTranslate; property: "y"; to: 0; duration: 155; easing.type: Easing.OutCubic }
        }
    }

    Component.onCompleted: loadConfig()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 22
        spacing: 12

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 70
            Layout.minimumHeight: 70
            Layout.maximumHeight: 70
            radius: 3
            color: (themeColor("#252525", "#ffffff", "#192543", "#ffffff"))
            border.width: 1
            border.color: (themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2"))

            RowLayout {
                anchors.fill: parent
                anchors.margins: 14
                spacing: 10

                ColumnLayout {
                    spacing: 2
                    Label {
                        text: "常驻 ATK 计算器"
                        color: (themeColor("#e1e1e3", "#1b1b1b", "#f3f7fd", "#18223e"))
                        font.pixelSize: 17
                        font.weight: Font.DemiBold
                    }
                    Label {
                        text: "白值 × (1 + 武器 ATK% + 圣遗物 ATK%) + 固定 ATK"
                        color: (themeColor("#909095", "#616161", "#8293ae", "#5f6f89"))
                        font.pixelSize: 11
                    }
                }

                Item { Layout.fillWidth: true }

                AppButton {
                    id: atkPercentModeButton
                    Layout.preferredWidth: 110
                    Layout.preferredHeight: 36
                    onClicked: togglePercentModeAnimated()
                    contentItem: Text {
                        id: percentModeButtonText
                        anchors.fill: parent
                        text: percentMode ? "百分数输入" : "小数输入"
                        transform: Translate { id: percentModeButtonTranslate }
                        color: (themeColor("#e7e7e8", "#1b1b1b", "#f3f7fd", "#18223e"))
                        font.pixelSize: 11
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: 3
                        color: atkPercentModeButton.down
                            ? (themeColor("#252525", "#f2f2f2", "#344a72", "#eaf0f7"))
                            : (atkPercentModeButton.hovered ? (themeColor("#383838", "#f7f7f7", "#2a3d63", "#f4f7fb")) : (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff")))
                        border.width: 1
                        border.color: atkPercentModeButton.hovered ? (themeColor("#707076", "#adadad", "#5874a3", "#9db3ce")) : (themeColor("#5b5b61", "#c0c0c0", "#3a5077", "#cfdceb"))
                        Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                        Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 82
            Layout.minimumHeight: 82
            Layout.maximumHeight: 82
            spacing: 10

            Repeater {
                model: [
                    {"key": "base_atk", "label": "白值", "hint": "角色基础 + 武器基础"},
                    {"key": "weapon_secondary", "label": "武器副词条 ATK%", "hint": percentMode ? "46.6 表示 46.6%" : "0.466 表示 46.6%"}
                ]
                delegate: Rectangle {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 10
                    color: input.activeFocus ? (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff")) : (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff"))
                    border.width: 1
                    border.color: input.activeFocus ? (themeColor("#707070", "#7a7a7a", "#62bfe8", "#5478b5")) : (themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2"))

                    Label {
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.leftMargin: 12
                        anchors.topMargin: 9
                        text: modelData.label
                        color: (themeColor("#d6d6d8", "#323232", "#b1c0d7", "#5f6f89"))
                        font.pixelSize: 12
                    }
                    Label {
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.rightMargin: 12
                        anchors.topMargin: 9
                        text: modelData.hint
                        color: (themeColor("#8b8b90", "#727272", "#8293ae", "#8795aa"))
                        font.pixelSize: 10
                    }
                    TextInput {
                        id: input
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.margins: 12
                        height: 25
                        text: config[modelData.key] !== undefined ? String(config[modelData.key]) : ""
                        color: (themeColor("#e7e7e8", "#1b1b1b", "#f3f7fd", "#18223e"))
                        selectionColor: (themeColor("#dfdfdf", "#202020", "#55d7fa", "#30488f"))
                        selectedTextColor: (themeColor("#202020", "#ffffff", "#0f1529", "#f8fbff"))
                        selectByMouse: true
                        font.pixelSize: 14
                        verticalAlignment: TextInput.AlignVCenter
                        onTextEdited: config[modelData.key] = text
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

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 225
            Layout.minimumHeight: 225
            Layout.maximumHeight: 225
            spacing: 8

            Repeater {
                model: artifacts

                delegate: Rectangle {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: modelData.fields.length === 2 ? 168 : 225
                    Layout.minimumHeight: Layout.preferredHeight
                    Layout.maximumHeight: Layout.preferredHeight
                    Layout.alignment: Qt.AlignTop
                    radius: 3
                    color: (themeColor("#252525", "#ffffff", "#192543", "#ffffff"))
                    border.width: 1
                    border.color: (themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2"))

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 11
                        spacing: 7

                        Label {
                            text: modelData.name
                            color: (themeColor("#d6d6d8", "#323232", "#b1c0d7", "#5f6f89"))
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                            Layout.alignment: Qt.AlignHCenter
                        }

                        Repeater {
                            model: modelData.fields

                            delegate: ColumnLayout {
                                required property string modelData
                                property string artifactKey: parent.parent.modelData.key
                                Layout.fillWidth: true
                                spacing: 3

                                Label {
                                    text: fieldLabel(modelData)
                                    color: (themeColor("#8c8c91", "#727272", "#8293ae", "#8795aa"))
                                    font.pixelSize: 10
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 4

                                    AppCheckBox {
                                        checked: config[artifactKey] !== undefined
                                            && config[artifactKey][modelData] !== undefined
                                            && config[artifactKey][modelData].checked
                                        enabled: !(artifactKey === "plume" && modelData === "main_flat")
                                        onToggled: config[artifactKey][modelData].checked = checked
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 31
                                        radius: 3
                                        color: (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff"))
                                        border.width: 1
                                        border.color: fieldInput.activeFocus ? (themeColor("#707070", "#7a7a7a", "#62bfe8", "#5478b5")) : (themeColor("#4a4a4a", "#d5d5d5", "#3a5077", "#cfdceb"))

                                        TextInput {
                                            id: fieldInput
                                            anchors.fill: parent
                                            anchors.leftMargin: 8
                                            anchors.rightMargin: 8
                                            text: config[artifactKey] !== undefined
                                                && config[artifactKey][modelData] !== undefined
                                                ? String(config[artifactKey][modelData].value)
                                                : "0"
                                            color: (themeColor("#e1e1e3", "#1b1b1b", "#f3f7fd", "#18223e"))
                                            selectByMouse: true
                                            font.pixelSize: 12
                                            verticalAlignment: TextInput.AlignVCenter
                                            onTextEdited: config[artifactKey][modelData].value = text
                                        }
                                        MouseArea {
                                            anchors.fill: fieldInput
                                            acceptedButtons: Qt.NoButton
                                            hoverEnabled: true
                                            cursorShape: Qt.IBeamCursor
                                        }
                                    }
                                }
                            }
                        }

                        Item { Layout.fillHeight: true }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 145
            Layout.minimumHeight: 145
            Layout.maximumHeight: 145
            radius: 3
            color: resultVisible ? (themeColor("#252525", "#ffffff", "#192543", "#ffffff")) : (themeColor("#252525", "#ffffff", "#192543", "#ffffff"))
            border.width: 1
            border.color: resultVisible ? (themeColor("#686868", "#303030", "#62bfe8", "#30488f")) : (themeColor("#3f3f3f", "#e2e2e2", "#304466", "#dee8f2"))

            Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 180 } }
            Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 180 } }

            RowLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 14

                ColumnLayout {
                    spacing: 3
                    Label {
                        text: errorText !== "" ? "输入错误" : "常驻 ATK"
                        color: errorText !== "" ? (themeColor("#ffaaa0", "#e7a79a", "#ff9a91", "#e77e78")) : (themeColor("#dddddf", "#222220", "#dbe5f3", "#24304a"))
                        font.pixelSize: 12
                    }
                    Label {
                        text: errorText !== "" ? errorText : (resultVisible ? formatNumber(result.finalAtk, 5) : "等待计算")
                        color: (themeColor("#dfdfe1", "#20201e", "#f3f7fd", "#18223e"))
                        font.pixelSize: resultVisible ? 29 : 19
                        font.weight: Font.DemiBold
                    }
                    Label {
                        visible: resultVisible
                        text: resultVisible
                            ? "总 ATK% " + formatNumber(result.totalPercent * 100, 5) + "% · 固定 ATK " + formatNumber(result.totalFlat, 5)
                            : ""
                        color: (themeColor("#9a9a9f", "#666666", "#8293ae", "#8795aa"))
                        font.pixelSize: 11
                    }
                }

                Item { Layout.fillWidth: true }

                AppButton {
                    id: fillMaxedButton
                    Layout.preferredWidth: 110
                    Layout.preferredHeight: 40
                    onClicked: fillMaxedMainStats()
                    contentItem: Text {
                        anchors.fill: parent
                        text: "满级主词条"
                        color: (themeColor("#d6d6d8", "#323232", "#b1c0d7", "#5f6f89"))
                        font.pixelSize: 11
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: 3
                        color: fillMaxedButton.down
                            ? (themeColor("#383838", "#f2f2f2", "#344a72", "#eaf0f7"))
                            : (fillMaxedButton.hovered ? (themeColor("#333333", "#f7f7f7", "#2a3d63", "#f4f7fb")) : (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff")))
                        border.width: 1
                        border.color: fillMaxedButton.hovered ? (themeColor("#75757b", "#adadad", "#5874a3", "#9db3ce")) : (themeColor("#555555", "#e2e2e2", "#3a5077", "#d5e0ec"))
                        Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                        Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                    }
                }

                AppButton {
                    id: saveAtkConfigButton
                    Layout.preferredWidth: 96
                    Layout.preferredHeight: 40
                    onClicked: saveConfig(true)
                    contentItem: Text {
                        anchors.fill: parent
                        text: "保存配置"
                        color: (themeColor("#d6d6d8", "#323232", "#b1c0d7", "#5f6f89"))
                        font.pixelSize: 11
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: 3
                        color: saveAtkConfigButton.down
                            ? (themeColor("#383838", "#f2f2f2", "#344a72", "#eaf0f7"))
                            : (saveAtkConfigButton.hovered ? (themeColor("#333333", "#f7f7f7", "#2a3d63", "#f4f7fb")) : (themeColor("#2b2b2b", "#ffffff", "#223253", "#fbfdff")))
                        border.width: 1
                        border.color: saveAtkConfigButton.hovered ? (themeColor("#75757b", "#adadad", "#5874a3", "#9db3ce")) : (themeColor("#555555", "#e2e2e2", "#3a5077", "#d5e0ec"))
                        Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                        Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                    }
                }

                AppButton {
                    id: calculateAtkButton
                    objectName: "calculateAtkButton"
                    Layout.preferredWidth: 112
                    Layout.preferredHeight: 46
                    hoverEnabled: true
                    focusPolicy: Qt.NoFocus
                    onClicked: calculateAtk()
                    contentItem: Text {
                        anchors.fill: parent
                        text: "计算 ATK"
                        color: (themeColor("#f5f5f5", "#ffffff", "#ffffff", "#ffffff"))
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: 3
                        color: calculateAtkButton.down
                            ? (themeColor("#606060", "#454545", "#5b7ed0", "#263a77"))
                            : (calculateAtkButton.hovered ? (themeColor("#555555", "#3b3b3b", "#4d6fc3", "#3d5caa")) : (themeColor("#4a4a4a", "#323232", "#3d5caa", "#30488f")))
                        border.width: 1
                        border.color: calculateAtkButton.hovered ? (themeColor("#787878", "#444444", "#6a89ba", "#3d5caa")) : (themeColor("#686868", "#2a2a2a", "#5874a3", "#263a77"))
                        Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                        Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                    }
                }

                AppButton {
                    id: applyToDamageButton
                    objectName: "applyToDamageButton"
                    Layout.preferredWidth: 142
                    Layout.preferredHeight: 46
                    enabled: resultVisible
                    hoverEnabled: true
                    focusPolicy: Qt.NoFocus
                    onClicked: applyResult()
                    contentItem: Text {
                        anchors.fill: parent
                        text: "应用到伤害计算器"
                        color: applyToDamageButton.enabled ? (themeColor("#f5f5f5", "#ffffff", "#ffffff", "#ffffff")) : (themeColor("#909090", "#8a8a8a", "#66758e", "#aab4c2"))
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: 3
                        color: !applyToDamageButton.enabled
                            ? (themeColor("#252525", "#fafafa", "#192543", "#f8fbff"))
                            : (applyToDamageButton.down
                                ? (themeColor("#606060", "#454545", "#5b7ed0", "#263a77"))
                                : (applyToDamageButton.hovered ? (themeColor("#555555", "#3b3b3b", "#4d6fc3", "#3d5caa")) : (themeColor("#4a4a4a", "#323232", "#3d5caa", "#30488f"))))
                        border.width: 1
                        border.color: !applyToDamageButton.enabled
                            ? (themeColor("#383838", "#e5e5e5", "#304466", "#dee8f2"))
                            : (applyToDamageButton.hovered ? (themeColor("#787878", "#444444", "#6a89ba", "#3d5caa")) : (themeColor("#686868", "#2a2a2a", "#5874a3", "#263a77")))
                        Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                        Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }
    }
}

