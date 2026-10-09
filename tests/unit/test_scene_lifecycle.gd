extends GdUnitTestSuite


func test_scene_enters_tree_runs_ready_and_releases_child() -> void:
	var runner: GdUnitSceneRunner = scene_runner("res://tests/fixtures/input_probe.tscn")
	var root: Node = runner.scene()
	assert_bool(root.is_inside_tree()).is_true()
	assert_int(root.get("ready_count")).is_equal(1)

	var disposable := Node.new()
	root.add_child(disposable)
	assert_bool(disposable.is_inside_tree()).is_true()
	disposable.queue_free()
	await get_tree().process_frame
	assert_bool(is_instance_valid(disposable)).is_false()


func test_child_signal_reaches_parent_once() -> void:
	var runner: GdUnitSceneRunner = scene_runner("res://tests/fixtures/input_probe.tscn")
	var root: Node = runner.scene()
	var source: Node = root.get_node("SignalSource")

	source.call("trigger")
	assert_int(root.get("observed_signal_count")).is_equal(1)
