import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    signal applyToDamage(string atkValue, string baseValue)

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
            color: "#ffffff"
            border.width: 1
            border.color: "#d5d5d0"

            RowLayout {
                anchors.fill: parent
                anchors.margins: 14
                spacing: 10

                ColumnLayout {
                    spacing: 2
                    Label {
                        text: "常驻 ATK 计算器"
                        color: "#1e1e1c"
                        font.pixelSize: 17
                        font.weight: Font.DemiBold
                    }
                    Label {
                        text: "白值 × (1 + 武器 ATK% + 圣遗物 ATK%) + 固定 ATK"
                        color: "#6f6f6a"
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
                        color: "#181817"
                        font.pixelSize: 11
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: 3
                        color: atkPercentModeButton.down
                            ? "#fafafa"
                            : (atkPercentModeButton.hovered ? "#f4f4f4" : "#f7f7f7")
                        border.width: 1
                        border.color: atkPercentModeButton.hovered ? "#8f8f89" : "#a4a49e"
                        Behavior on color { ColorAnimation { duration: 110 } }
                        Behavior on border.color { ColorAnimation { duration: 110 } }
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
                    color: input.activeFocus ? "#ffffff" : "#ffffff"
                    border.width: 1
                    border.color: input.activeFocus ? "#282826" : "#d5d5d0"

                    Label {
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.leftMargin: 12
                        anchors.topMargin: 9
                        text: modelData.label
                        color: "#292927"
                        font.pixelSize: 12
                    }
                    Label {
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.rightMargin: 12
                        anchors.topMargin: 9
                        text: modelData.hint
                        color: "#74746f"
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
                        color: "#181817"
                        selectionColor: "#202020"
                        selectedTextColor: "#ffffff"
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
                    color: "#ffffff"
                    border.width: 1
                    border.color: "#d5d5d0"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 11
                        spacing: 7

                        Label {
                            text: modelData.name
                            color: "#292927"
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
                                    color: "#73736e"
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
                                        color: "#ffffff"
                                        border.width: 1
                                        border.color: fieldInput.activeFocus ? "#282826" : "#c7c7c1"

                                        TextInput {
                                            id: fieldInput
                                            anchors.fill: parent
                                            anchors.leftMargin: 8
                                            anchors.rightMargin: 8
                                            text: config[artifactKey] !== undefined
                                                && config[artifactKey][modelData] !== undefined
                                                ? String(config[artifactKey][modelData].value)
                                                : "0"
                                            color: "#1e1e1c"
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
            color: resultVisible ? "#ffffff" : "#ffffff"
            border.width: 1
            border.color: resultVisible ? "#303030" : "#d5d5d0"

            Behavior on color { ColorAnimation { duration: 180 } }
            Behavior on border.color { ColorAnimation { duration: 180 } }

            RowLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 14

                ColumnLayout {
                    spacing: 3
                    Label {
                        text: errorText !== "" ? "输入错误" : "常驻 ATK"
                        color: errorText !== "" ? "#e7a79a" : "#222220"
                        font.pixelSize: 12
                    }
                    Label {
                        text: errorText !== "" ? errorText : (resultVisible ? formatNumber(result.finalAtk, 5) : "等待计算")
                        color: "#20201e"
                        font.pixelSize: resultVisible ? 29 : 19
                        font.weight: Font.DemiBold
                    }
                    Label {
                        visible: resultVisible
                        text: resultVisible
                            ? "总 ATK% " + formatNumber(result.totalPercent * 100, 5) + "% · 固定 ATK " + formatNumber(result.totalFlat, 5)
                            : ""
                        color: "#656560"
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
                        color: "#292927"
                        font.pixelSize: 11
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: 3
                        color: fillMaxedButton.down
                            ? "#fafafa"
                            : (fillMaxedButton.hovered ? "#f7f7f7" : "#ffffff")
                        border.width: 1
                        border.color: fillMaxedButton.hovered ? "#8a8a84" : "#bdbdb7"
                        Behavior on color { ColorAnimation { duration: 110 } }
                        Behavior on border.color { ColorAnimation { duration: 110 } }
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
                        color: "#292927"
                        font.pixelSize: 11
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: 3
                        color: saveAtkConfigButton.down
                            ? "#fafafa"
                            : (saveAtkConfigButton.hovered ? "#f7f7f7" : "#ffffff")
                        border.width: 1
                        border.color: saveAtkConfigButton.hovered ? "#8a8a84" : "#bdbdb7"
                        Behavior on color { ColorAnimation { duration: 110 } }
                        Behavior on border.color { ColorAnimation { duration: 110 } }
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
                        color: "#ffffff"
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: 3
                        color: calculateAtkButton.down
                            ? "#363634"
                            : (calculateAtkButton.hovered ? "#20201e" : "#1a1a1a")
                        border.width: 1
                        border.color: calculateAtkButton.hovered ? "#171717" : "#242422"
                        Behavior on color { ColorAnimation { duration: 110 } }
                        Behavior on border.color { ColorAnimation { duration: 110 } }
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
                        color: applyToDamageButton.enabled ? "#ffffff" : "#85857f"
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: 3
                        color: !applyToDamageButton.enabled
                            ? "#fafafa"
                            : (applyToDamageButton.down
                                ? "#30302e"
                                : (applyToDamageButton.hovered ? "#161616" : "#252525"))
                        border.width: 1
                        border.color: !applyToDamageButton.enabled
                            ? "#d2d2cd"
                            : (applyToDamageButton.hovered ? "#171717" : "#1d1d1b")
                        Behavior on color { ColorAnimation { duration: 110 } }
                        Behavior on border.color { ColorAnimation { duration: 110 } }
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }
    }
}

