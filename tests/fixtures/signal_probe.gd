extends Node

signal probe_signal


func trigger() -> void:
	probe_signal.emit()
