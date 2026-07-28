import QtQuick
import QtQuick.Controls

AbstractButton {
    id: control
    checkable: true
    hoverEnabled: true
    focusPolicy: Qt.NoFocus
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
                ? "#f8f8f8"
                : (control.checked
                    ? (control.hovered ? "#323230" : "#2a2a28")
                    : (control.hovered ? "#fafafa" : "#ffffff"))
            border.width: 1
            border.color: !control.enabled
                ? "#c1c1bb"
                : (control.checked
                    ? (control.hovered ? "#171717" : "#1f1f1d")
                    : (control.hovered ? "#898983" : "#adada7"))

            Text {
                anchors.centerIn: parent
                text: "✓"
                visible: control.checked
                color: control.enabled ? "#ffffff" : "#7d7d77"
                font.pixelSize: 12
                font.weight: Font.Bold
            }

            Behavior on color { ColorAnimation { duration: 100 } }
            Behavior on border.color { ColorAnimation { duration: 100 } }
        }

        Text {
            id: checkLabel
            anchors.left: checkIndicator.right
            anchors.leftMargin: control.text === "" ? 0 : control.spacing
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            text: control.text
            font: control.font
            color: control.enabled ? "#292927" : "#81817b"
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

