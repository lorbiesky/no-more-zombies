extends GdUnitTestSuite


func test_action_press_hold_and_release_reach_scene() -> void:
	var runner: GdUnitSceneRunner = scene_runner("res://tests/fixtures/input_probe.tscn")
	var root: Node = runner.scene()

	runner.simulate_action_press("ui_accept")
	await runner.await_input_processed()
	assert_bool(Input.is_action_pressed("ui_accept")).is_true()
	assert_int(root.get("press_count")).is_equal(1)

	await runner.simulate_frames(2)
	assert_bool(Input.is_action_pressed("ui_accept")).is_true()
	assert_int(root.get("press_count")).is_equal(1)

	runner.simulate_action_release("ui_accept")
	await runner.await_input_processed()
	assert_bool(Input.is_action_pressed("ui_accept")).is_false()
	assert_int(root.get("release_count")).is_equal(1)
