import QtQuick
import QtQuick.Controls

AbstractButton {
    id: control
    checkable: true
    hoverEnabled: true
    focusPolicy: Qt.NoFocus
    readonly property bool darkMode: ApplicationWindow.window
        ? Boolean(ApplicationWindow.window.darkMode)
        : false
    readonly property bool furinaTheme: ApplicationWindow.window
        ? Boolean(ApplicationWindow.window.furinaTheme)
        : false
    readonly property bool themeTransitionRunning: ApplicationWindow.window
        ? Boolean(ApplicationWindow.window.themeTransitionRunning)
        : false

    function themeColor(defaultDark, defaultLight, furinaDark, furinaLight) {
        return furinaTheme
            ? (darkMode ? furinaDark : furinaLight)
            : (darkMode ? defaultDark : defaultLight)
    }
    spacing: 6

    implicitWidth: contentItem.implicitWidth
    implicitHeight: contentItem.implicitHeight

    contentItem: Item {
        implicitWidth: checkIndicator.implicitWidth
            + (control.text === "" ? 0 : control.spacing + checkLabel.implicitWidth)
        implicitHeight: Math.max(checkIndicator.implicitHeight, checkLabel.implicitHeight)

        Rectangle {
            id: checkIndicator
            implicitWidth: 18
            implicitHeight: 18
            width: implicitWidth
            height: implicitHeight
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            radius: 2
            color: !control.enabled
                ? (themeColor("#252525", "#fafafa", "#192543", "#f8fbff"))
                : (control.checked
                    ? (control.hovered ? (themeColor("#555555", "#3b3b3b", "#4d6fc3", "#3d5caa")) : (themeColor("#4a4a4a", "#323232", "#3d5caa", "#30488f")))
                    : (control.hovered ? (themeColor("#333333", "#f7f7f7", "#2a3d63", "#f4f7fb")) : (themeColor("#2b2b2b", "#ffffff", "#223253", "#ffffff"))))
            border.width: 1
            border.color: !control.enabled
                ? (themeColor("#383838", "#e5e5e5", "#304466", "#dee8f2"))
                : (control.checked
                    ? (control.hovered ? (themeColor("#787878", "#444444", "#6a89ba", "#3d5caa")) : (themeColor("#686868", "#2a2a2a", "#5874a3", "#263a77")))
                    : (control.hovered ? (themeColor("#5a5a5a", "#b8b8b8", "#5874a3", "#9db3ce")) : (themeColor("#4a4a4a", "#d8d8d8", "#3a5077", "#d5e0ec"))))

            Text {
                anchors.centerIn: parent
                text: "✓"
                visible: control.checked
                color: control.enabled ? (themeColor("#f5f5f5", "#ffffff", "#ffffff", "#ffffff")) : (themeColor("#909090", "#8a8a8a", "#66758e", "#aab4c2"))
                font.pixelSize: 12
                font.weight: Font.Bold
            }

            Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 100 } }
            Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 100 } }
        }

        Text {
            id: checkLabel
            anchors.left: checkIndicator.right
            anchors.leftMargin: control.text === "" ? 0 : control.spacing
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            text: control.text
            font: control.font
            color: control.enabled ? (themeColor("#f1f1f1", "#323232", "#f3f7fd", "#5f6f89")) : (themeColor("#909090", "#8a8a8a", "#66758e", "#aab4c2"))
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }

    background: Item {}

    MouseArea {
        anchors.fill: parent
        z: 1000
        enabled: control.enabled
        acceptedButtons: Qt.NoButton
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
    }
}

