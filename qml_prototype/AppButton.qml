import QtQuick
import QtQuick.Controls

AbstractButton {
    id: control
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

    implicitWidth: Math.max(
        background ? background.implicitWidth : 0,
        contentItem ? contentItem.implicitWidth + leftPadding + rightPadding : 0
    )
    implicitHeight: Math.max(
        background ? background.implicitHeight : 0,
        contentItem ? contentItem.implicitHeight + topPadding + bottomPadding : 0
    )

    contentItem: Text {
        text: control.text
        font: control.font
        color: control.enabled ? (themeColor("#f1f1f1", "#1b1b1b", "#f3f7fd", "#18223e")) : (themeColor("#909090", "#8a8a8a", "#66758e", "#aab4c2"))
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        implicitWidth: 88
        implicitHeight: 36
        radius: 2
        color: !control.enabled
            ? (themeColor("#252525", "#fafafa", "#192543", "#f8fbff"))
            : (control.down
                ? (themeColor("#3d3d3d", "#f2f2f2", "#344a72", "#eaf0f7"))
                : (control.hovered ? (themeColor("#333333", "#f7f7f7", "#2a3d63", "#f4f7fb")) : (themeColor("#2b2b2b", "#ffffff", "#223253", "#ffffff"))))
        border.width: 1
        border.color: !control.enabled
            ? (themeColor("#383838", "#e5e5e5", "#304466", "#dee8f2"))
            : (control.hovered ? (themeColor("#5a5a5a", "#b8b8b8", "#5874a3", "#9db3ce")) : (themeColor("#3f3f3f", "#d8d8d8", "#3a5077", "#d5e0ec")))
        Behavior on color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
        Behavior on border.color { enabled: !themeTransitionRunning; ColorAnimation { duration: 110 } }
    }

    MouseArea {
        anchors.fill: parent
        z: 1000
        enabled: control.enabled
        acceptedButtons: Qt.NoButton
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
    }
}
