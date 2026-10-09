extends Node

var ready_count: int = 0
var press_count: int = 0
var release_count: int = 0
var observed_signal_count: int = 0


func _ready() -> void:
	ready_count += 1
	var signal_source: Node = get_node("SignalSource")
	signal_source.connect("probe_signal", _on_probe_signal)


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		press_count += 1
	elif event.is_action_released("ui_accept"):
		release_count += 1


func _on_probe_signal() -> void:
	observed_signal_count += 1
