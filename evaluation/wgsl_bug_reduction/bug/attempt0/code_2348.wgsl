@group(0) @binding(1) var<storage, read_write> input_data: array<i32>;
@group(0) @binding(0) var<storage, read_write> output_data: array<i32>;

@compute @workgroup_size(1)
fn control_flow( @builtin(global_invocation_id) id: vec3u ) {
	var cntrl_ix: i32 = -1; // always incremented before use
	var output_ix: i32 = 0;
	var cntrl_val: i32;
	cntrl_ix++;
	cntrl_val = input_data[cntrl_ix];
	loop {
		// ------ BLOCK 1 -------
		output_data[output_ix] = 1;
		output_ix++;
		// -----------------------
		if cntrl_val != 1 {
			break;
		}
		// ------ BLOCK 3 -------
		output_data[output_ix] = 3;
		output_ix++;
		// -----------------------
		cntrl_ix++;
		cntrl_val = input_data[cntrl_ix];
		if (cntrl_val == 1) {
			cntrl_ix++;
			cntrl_val = input_data[cntrl_ix];
			loop {
				// ------ BLOCK 5 -------
				output_data[output_ix] = 5;
				output_ix++;
				// -----------------------
				if cntrl_val != 1 {
					break;
				}
				// ------ BLOCK 11 -------
				output_data[output_ix] = 11;
				output_ix++;
				// -----------------------
				cntrl_ix++;
				cntrl_val = input_data[cntrl_ix];
				if (cntrl_val == 1) {
					// ------ BLOCK 24 -------
					output_data[output_ix] = 24;
					output_ix++;
					// -----------------------
				}
				else {
					// ------ BLOCK 23 -------
					output_data[output_ix] = 23;
					output_ix++;
					// -----------------------
				}
				// ------ BLOCK 25 -------
				output_data[output_ix] = 25;
				output_ix++;
				// -----------------------
				continuing {
					if cntrl_val != -1 {
						cntrl_ix++;
						cntrl_val = input_data[cntrl_ix];
					}
					break if cntrl_val == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
				}
			}
			// ------ BLOCK 10 -------
			output_data[output_ix] = 10;
			output_ix++;
			// -----------------------
			cntrl_ix++;
			cntrl_val = input_data[cntrl_ix];
			switch (cntrl_val) {
				case 0: {
					// ------ BLOCK 26 -------
					output_data[output_ix] = 26;
					output_ix++;
					// -----------------------
				}
				case 1: {
					// ------ BLOCK 27 -------
					output_data[output_ix] = 27;
					output_ix++;
					// -----------------------
				}
				case 2: {
					// ------ BLOCK 28 -------
					output_data[output_ix] = 28;
					output_ix++;
					// -----------------------
				}
				case 3: {
					// ------ BLOCK 29 -------
					output_data[output_ix] = 29;
					output_ix++;
					// -----------------------
				}
				default: {
					// ------ BLOCK 30 -------
					output_data[output_ix] = 30;
					output_ix++;
					// -----------------------
				}
			}
			// ------ BLOCK 31 -------
			output_data[output_ix] = 31;
			output_ix++;
			// -----------------------
		}
		else {
			// ------ BLOCK 4 -------
			output_data[output_ix] = 4;
			output_ix++;
			// -----------------------
			cntrl_ix++;
			cntrl_val = input_data[cntrl_ix];
			loop {
				// ------ BLOCK 12 -------
				output_data[output_ix] = 12;
				output_ix++;
				// -----------------------
				if cntrl_val != 1 {
					break;
				}
				// ------ BLOCK 33 -------
				output_data[output_ix] = 33;
				output_ix++;
				// -----------------------
				continuing {
					if cntrl_val != -1 {
						cntrl_ix++;
						cntrl_val = input_data[cntrl_ix];
					}
					break if cntrl_val == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
				}
			}
			// ------ BLOCK 32 -------
			output_data[output_ix] = 32;
			output_ix++;
			// -----------------------
		}
		// ------ BLOCK 6 -------
		output_data[output_ix] = 6;
		output_ix++;
		// -----------------------
		cntrl_ix++;
		cntrl_val = input_data[cntrl_ix];
		switch (cntrl_val) {
			case 0: {
				// ------ BLOCK 13 -------
				output_data[output_ix] = 13;
				output_ix++;
				// -----------------------
				cntrl_ix++;
				cntrl_val = input_data[cntrl_ix];
				if (cntrl_val == 1) {
					// ------ BLOCK 35 -------
					output_data[output_ix] = 35;
					output_ix++;
					// -----------------------
				}
				else {
					// ------ BLOCK 34 -------
					output_data[output_ix] = 34;
					output_ix++;
					// -----------------------
				}
				// ------ BLOCK 36 -------
				output_data[output_ix] = 36;
				output_ix++;
				// -----------------------
			}
			case 1: {
				cntrl_ix++;
				cntrl_val = input_data[cntrl_ix];
				loop {
					// ------ BLOCK 14 -------
					output_data[output_ix] = 14;
					output_ix++;
					// -----------------------
					if cntrl_val != 1 {
						break;
					}
					// ------ BLOCK 38 -------
					output_data[output_ix] = 38;
					output_ix++;
					// -----------------------
					continuing {
						if cntrl_val != -1 {
							cntrl_ix++;
							cntrl_val = input_data[cntrl_ix];
						}
						break if cntrl_val == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
					}
				}
				// ------ BLOCK 37 -------
				output_data[output_ix] = 37;
				output_ix++;
				// -----------------------
			}
			case 2: {
				cntrl_ix++;
				cntrl_val = input_data[cntrl_ix];
				loop {
					// ------ BLOCK 15 -------
					output_data[output_ix] = 15;
					output_ix++;
					// -----------------------
					if cntrl_val != 1 {
						break;
					}
					// ------ BLOCK 40 -------
					output_data[output_ix] = 40;
					output_ix++;
					// -----------------------
					continuing {
						if cntrl_val != -1 {
							cntrl_ix++;
							cntrl_val = input_data[cntrl_ix];
						}
						break if cntrl_val == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
					}
				}
				// ------ BLOCK 39 -------
				output_data[output_ix] = 39;
				output_ix++;
				// -----------------------
			}
			case 3: {
				// ------ BLOCK 16 -------
				output_data[output_ix] = 16;
				output_ix++;
				// -----------------------
				// ------ BLOCK 41 -------
				output_data[output_ix] = 41;
				output_ix++;
				// -----------------------
			}
			default: {
				cntrl_ix++;
				cntrl_val = input_data[cntrl_ix];
				loop {
					// ------ BLOCK 17 -------
					output_data[output_ix] = 17;
					output_ix++;
					// -----------------------
					if cntrl_val != 1 {
						break;
					}
					// ------ BLOCK 43 -------
					output_data[output_ix] = 43;
					output_ix++;
					// -----------------------
					continuing {
						if cntrl_val != -1 {
							cntrl_ix++;
							cntrl_val = input_data[cntrl_ix];
						}
						break if cntrl_val == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
					}
				}
				// ------ BLOCK 42 -------
				output_data[output_ix] = 42;
				output_ix++;
				// -----------------------
			}
		}
		// ------ BLOCK 18 -------
		output_data[output_ix] = 18;
		output_ix++;
		// -----------------------
		cntrl_ix++;
		cntrl_val = input_data[cntrl_ix];
		switch (cntrl_val) {
			case 0: {
				// ------ BLOCK 44 -------
				output_data[output_ix] = 44;
				output_ix++;
				// -----------------------
			}
			case 1: {
				// ------ BLOCK 45 -------
				output_data[output_ix] = 45;
				output_ix++;
				// -----------------------
			}
			case 2: {
				// ------ BLOCK 46 -------
				output_data[output_ix] = 46;
				output_ix++;
				// -----------------------
			}
			case 3: {
				// ------ BLOCK 47 -------
				output_data[output_ix] = 47;
				output_ix++;
				// -----------------------
			}
			default: {
				// ------ BLOCK 48 -------
				output_data[output_ix] = 48;
				output_ix++;
				// -----------------------
			}
		}
		// ------ BLOCK 49 -------
		output_data[output_ix] = 49;
		output_ix++;
		// -----------------------
		continuing {
			if cntrl_val != -1 {
				cntrl_ix++;
				cntrl_val = input_data[cntrl_ix];
			}
			break if cntrl_val == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
		}
	}
	// ------ BLOCK 2 -------
	output_data[output_ix] = 2;
	output_ix++;
	// -----------------------
	cntrl_ix++;
	cntrl_val = input_data[cntrl_ix];
	switch (cntrl_val) {
		case 0: {
			// ------ BLOCK 7 -------
			output_data[output_ix] = 7;
			output_ix++;
			// -----------------------
			// ------ BLOCK 19 -------
			output_data[output_ix] = 19;
			output_ix++;
			// -----------------------
			cntrl_ix++;
			cntrl_val = input_data[cntrl_ix];
			if (cntrl_val == 1) {
				// ------ BLOCK 51 -------
				output_data[output_ix] = 51;
				output_ix++;
				// -----------------------
			}
			else {
				// ------ BLOCK 50 -------
				output_data[output_ix] = 50;
				output_ix++;
				// -----------------------
			}
			// ------ BLOCK 52 -------
			output_data[output_ix] = 52;
			output_ix++;
			// -----------------------
		}
		default: {
			cntrl_ix++;
			cntrl_val = input_data[cntrl_ix];
			loop {
				// ------ BLOCK 8 -------
				output_data[output_ix] = 8;
				output_ix++;
				// -----------------------
				if cntrl_val != 1 {
					break;
				}
				cntrl_ix++;
				cntrl_val = input_data[cntrl_ix];
				loop {
					// ------ BLOCK 21 -------
					output_data[output_ix] = 21;
					output_ix++;
					// -----------------------
					if cntrl_val != 1 {
						break;
					}
					// ------ BLOCK 54 -------
					output_data[output_ix] = 54;
					output_ix++;
					// -----------------------
					continuing {
						if cntrl_val != -1 {
							cntrl_ix++;
							cntrl_val = input_data[cntrl_ix];
						}
						break if cntrl_val == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
					}
				}
				// ------ BLOCK 53 -------
				output_data[output_ix] = 53;
				output_ix++;
				// -----------------------
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
				// ------ BLOCK 20 -------
				output_data[output_ix] = 20;
				output_ix++;
				// -----------------------
				if cntrl_val != 1 {
					break;
				}
				// ------ BLOCK 56 -------
				output_data[output_ix] = 56;
				output_ix++;
				// -----------------------
				continuing {
					if cntrl_val != -1 {
						cntrl_ix++;
						cntrl_val = input_data[cntrl_ix];
					}
					break if cntrl_val == -1; // way to break out of a loop while in a switch (`break` in a switch just leaves switch)
				}
			}
			// ------ BLOCK 55 -------
			output_data[output_ix] = 55;
			output_ix++;
			// -----------------------
		}
	}
	// ------ BLOCK 9 -------
	output_data[output_ix] = 9;
	output_ix++;
	// -----------------------
	// ------ BLOCK 22 -------
	output_data[output_ix] = 22;
	output_ix++;
	// -----------------------
	cntrl_ix++;
	cntrl_val = input_data[cntrl_ix];
	switch (cntrl_val) {
		case 0: {
			// ------ BLOCK 57 -------
			output_data[output_ix] = 57;
			output_ix++;
			// -----------------------
		}
		case 1: {
			// ------ BLOCK 58 -------
			output_data[output_ix] = 58;
			output_ix++;
			// -----------------------
		}
		case 2: {
			// ------ BLOCK 59 -------
			output_data[output_ix] = 59;
			output_ix++;
			// -----------------------
		}
		default: {
			// ------ BLOCK 60 -------
			output_data[output_ix] = 60;
			output_ix++;
			// -----------------------
		}
	}
	// ------ BLOCK 61 -------
	output_data[output_ix] = 61;
	output_ix++;
	// -----------------------
	return;
}