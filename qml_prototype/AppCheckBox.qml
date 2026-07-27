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
            radius: 4
            color: !control.enabled
                ? "#1b2638"
                : (control.checked
                    ? (control.hovered ? "#4f8ff0" : "#347fd8")
                    : (control.hovered ? "#1d3150" : "#111c2f"))
            border.width: 1
            border.color: !control.enabled
                ? "#344158"
                : (control.checked
                    ? (control.hovered ? "#9fc2ff" : "#72a7f3")
                    : (control.hovered ? "#6686b2" : "#405777"))

            Text {
                anchors.centerIn: parent
                text: "✓"
                visible: control.checked
                color: control.enabled ? "#ffffff" : "#7f8ca3"
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
            color: control.enabled ? "#dce8ff" : "#6f7d96"
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

