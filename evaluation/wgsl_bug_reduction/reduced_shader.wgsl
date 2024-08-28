@group(0) @binding(0) var<storage, read_write> output_data: array<i32>;
@group(0) @binding(1) var <storage, read_write> input_data: array<i32>;

@compute @workgroup_size(1)
fn control_flow(@builtin(global_invocation_id) id: vec3u) {
	var cntrl_ix: i32 = -1; // always incremented before use
	var output_ix: i32 = 0;
	var cntrl_val: i32; // assigned prior to use
	var use_input_data = input_data[0];
	cntrl_ix++;
	cntrl_val = input_data[cntrl_ix];
	loop {
		// ------ BLOCK 1 -------
		output_data[output_ix] = 1;
		output_ix++;
		// ------------------------
		if cntrl_val != 1 {
			break;
		}
		cntrl_ix++;
		cntrl_val = input_data[cntrl_ix];
		loop {
			// ------ BLOCK 3 -------
			output_data[output_ix] = 3;
			output_ix++;
			// ------------------------
			if cntrl_val != 1 {
				break;
			}
			// ------ BLOCK 5 -------
			output_data[output_ix] = 5;
			output_ix++;
			// ------------------------
			// ------ BLOCK 8 -------
			output_data[output_ix] = 8;
			output_ix++;
			// ------------------------
			// ------ BLOCK 17 -------
			output_data[output_ix] = 17;
			output_ix++;
			// ------------------------
			continuing {
				if cntrl_val != -1 {
					cntrl_ix++;
					cntrl_val = input_data[cntrl_ix];
				}
				break if cntrl_val == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
			}
		}
		// ------ BLOCK 4 -------
		output_data[output_ix] = 4;
		output_ix++;
		// ------------------------
		cntrl_ix++;
		cntrl_val = input_data[cntrl_ix];
		switch (cntrl_val) {
			case 0: {
				cntrl_ix++;
				cntrl_val = input_data[cntrl_ix];
				loop {
					// ------ BLOCK 9 -------
					output_data[output_ix] = 9;
					output_ix++;
					// ------------------------
					if cntrl_val != 1 {
						break;
					}
					// ------ BLOCK 19 -------
					output_data[output_ix] = 19;
					output_ix++;
					// ------------------------
					continuing {
						if cntrl_val != -1 {
							cntrl_ix++;
							cntrl_val = input_data[cntrl_ix];
						}
						break if cntrl_val == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
					}
				}
				// ------ BLOCK 18 -------
				output_data[output_ix] = 18;
				output_ix++;
				// ------------------------
			}
			case 1: {
				// ------ BLOCK 10 -------
				output_data[output_ix] = 10;
				output_ix++;
				// ------------------------
				cntrl_ix++;
				cntrl_val = input_data[cntrl_ix];
				if (cntrl_val == 1) {
					// ------ BLOCK 21 -------
					output_data[output_ix] = 21;
					output_ix++;
					// ------------------------
				}
				else {
					// ------ BLOCK 20 -------
					output_data[output_ix] = 20;
					output_ix++;
					// ------------------------
				}
				// ------ BLOCK 22 -------
				output_data[output_ix] = 22;
				output_ix++;
				// ------------------------
			}
			default: {
				// ------ BLOCK 23 -------
				output_data[output_ix] = 23;
				output_ix++;
				// ------------------------
			}
		}
		cntrl_ix++;
		cntrl_val = input_data[cntrl_ix];
		loop {
			// ------ BLOCK 12 -------
			output_data[output_ix] = 12;
			output_ix++;
			// ------------------------
			if cntrl_val != 1 {
				break;
			}
			// ------ BLOCK 26 -------
			output_data[output_ix] = 26;
			output_ix++;
			// ------------------------
			continuing {
				if cntrl_val != -1 {
					cntrl_ix++;
					cntrl_val = input_data[cntrl_ix];
				}
				break if cntrl_val == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
			}
		}
		// ------ BLOCK 25 -------
		output_data[output_ix] = 25;
		output_ix++;
		// ------------------------
		continuing {
			if cntrl_val != -1 {
				cntrl_ix++;
				cntrl_val = input_data[cntrl_ix];
			}
			break if cntrl_val == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
		}
	}
	cntrl_ix++;
	cntrl_val = input_data[cntrl_ix];
	loop {
		// ------ BLOCK 2 -------
		output_data[output_ix] = 2;
		output_ix++;
		// ------------------------
		if cntrl_val != 1 {
			break;
		}
		// ------ BLOCK 7 -------
		output_data[output_ix] = 7;
		output_ix++;
		// ------------------------
		continuing {
			if cntrl_val != -1 {
				cntrl_ix++;
				cntrl_val = input_data[cntrl_ix];
			}
			break if cntrl_val == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
		}
	}
	cntrl_ix++;
	cntrl_val = input_data[cntrl_ix];
	loop {
		// ------ BLOCK 6 -------
		output_data[output_ix] = 6;
		output_ix++;
		// ------------------------
		if cntrl_val != 1 {
			break;
		}
		// ------ BLOCK 16 -------
		output_data[output_ix] = 16;
		output_ix++;
		// ------------------------
		continuing {
			if cntrl_val != -1 {
				cntrl_ix++;
				cntrl_val = input_data[cntrl_ix];
			}
			break if cntrl_val == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
		}
	}
	// ------ BLOCK 15 -------
	output_data[output_ix] = 15;
	output_ix++;
	// ------------------------
	cntrl_ix++;
	cntrl_val = input_data[cntrl_ix];
	switch (cntrl_val) {
		case 0: {
			// ------ BLOCK 38 -------
			output_data[output_ix] = 38;
			output_ix++;
			// ------------------------
		}
		default: {
			// ------ BLOCK 39 -------
			output_data[output_ix] = 39;
			output_ix++;
			// ------------------------
		}
	}
	// ------ BLOCK 40 -------
	output_data[output_ix] = 40;
	output_ix++;
	// ------------------------
	return;
}