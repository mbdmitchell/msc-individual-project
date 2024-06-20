(module
	(import "js" "memory" (memory 0))
	(memory $outputMemory 1)
	(export "outputMemory" (memory $outputMemory))
	(global $elem_size i32 (i32.const 4))
	(func $byte_offset (param $index i32) (result i32)
		(i32.mul (local.get $index) (global.get $elem_size))
	)
	(func $inc (param $num i32) (result i32)
		(i32.add (local.get $num) (i32.const 1))
	)
	(func $calc_cntrl_val (param $index i32) (result i32)
		(i32.load
			(memory 0)
			(call $byte_offset(local.get $index))
		)
	)
	(func $store_in_output (param $index i32) (param $value i32)
		(i32.store
			(memory $outputMemory)
			(call $byte_offset (local.get $index))
			(local.get $value)
		)
	)
	(func $cf (export "cf")

		;; setup
		(local $output_index i32)
		(local $control_index i32)
		(local $control_val i32)
		(local.set $output_index (i32.const 0))
		(local.set $control_index (i32.const 0))
		(local.set $control_val (call $calc_cntrl_val (local.get $control_index)))

		;; control flow code
		;; NODE 1
		(call $store_in_output
			(local.get $output_index)
			(i32.const 1)
		)
		(local.set $output_index
			(call $inc (local.get $output_index))
		)
		(local.set $control_index
			(call $inc (local.get $control_index))
		)
		(block $switch0
			(block
				(block
					(block (local.get $control_val)
						(br_table
							0	 ;; case == 0 => (br 0)
							1	 ;; case == 1 => (br 1)
							2	 ;; default => (br 2)
						)
						;; guard from UB
						(call $store_in_output (local.get $output_index)(i32.const -1))
						(local.set $output_index (call $inc (local.get $output_index)))
						(br $switch0)
					)
					;; Target for (br 0)
					;; NODE 3
					(call $store_in_output
						(local.get $output_index)
						(i32.const 3)
					)
					(local.set $output_index
						(call $inc (local.get $output_index))
					)
					(local.set $control_index
						(call $inc (local.get $control_index))
					)
					(block $switch1
						(block
							(block
								(block
									(block (local.get $control_val)
										(br_table
											0	 ;; case == 0 => (br 0)
											1	 ;; case == 1 => (br 1)
											2	 ;; case == 2 => (br 2)
											3	 ;; default => (br 3)
										)
										;; guard from UB
										(call $store_in_output (local.get $output_index)(i32.const -1))
										(local.set $output_index (call $inc (local.get $output_index)))
										(br $switch1)
									)
									;; Target for (br 0)
									;; NODE 9
									(call $store_in_output
										(local.get $output_index)
										(i32.const 9)
									)
									(local.set $output_index
										(call $inc (local.get $output_index))
									)
									(return)
								)
								;; Target for (br 1)
								;; NODE 8
								(call $store_in_output
									(local.get $output_index)
									(i32.const 8)
								)
								(local.set $output_index
									(call $inc (local.get $output_index))
								)
								(return)
							)
							;; Target for (br 2)
							;; NODE 7
							(call $store_in_output
								(local.get $output_index)
								(i32.const 7)
							)
							(local.set $output_index
								(call $inc (local.get $output_index))
							)
							(return)
						)
						;; Target for (br 3) => default
						;; NODE 10
						(call $store_in_output
							(local.get $output_index)
							(i32.const 10)
						)
						(local.set $output_index
							(call $inc (local.get $output_index))
						)
						(return)
					)
					(br $switch0)
				)
				;; Target for (br 1)
				;; NODE 2
				(call $store_in_output
					(local.get $output_index)
					(i32.const 2)
				)
				(local.set $output_index
					(call $inc (local.get $output_index))
				)
				(local.set $control_val
					(call $calc_cntrl_val (local.get $control_index))
				)
				(local.set $control_index
					(call $inc (local.get $control_index))
				)
				(if (i32.eqz (local.get $control_val))
					(then
						;; NODE 5
						(call $store_in_output
							(local.get $output_index)
							(i32.const 5)
						)
						(local.set $output_index
							(call $inc (local.get $output_index))
						)
						(return)
					)
					(else
						;; NODE 6
						(call $store_in_output
							(local.get $output_index)
							(i32.const 6)
						)
						(local.set $output_index
							(call $inc (local.get $output_index))
						)
						(return)
					)
				)
				(br $switch0)
			)
			;; Target for (br 2) => default
			;; NODE 4
			(call $store_in_output
				(local.get $output_index)
				(i32.const 4)
			)
			(local.set $output_index
				(call $inc (local.get $output_index))
			)
			;; NODE 11
			(call $store_in_output
				(local.get $output_index)
				(i32.const 11)
			)
			(local.set $output_index
				(call $inc (local.get $output_index))
			)
			(return)
		)
	)
)