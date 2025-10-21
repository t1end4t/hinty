use anyhow::{Ok, Result, anyhow};

pub fn bead_sort(mut arr: Vec<i32>) -> Result<Vec<i32>> {
    let num_elements = arr.len();

    if arr.is_empty() {
        return Ok(vec![]);
    }
    let max_val = arr.iter().max().copied().unwrap() as usize;

    if arr.iter().any(|&x| x < 0) {
        return Err(anyhow!("Bead sort does not support negative number"));
    }

    let mut beads = vec![vec![0; max_val]; num_elements as usize];

    // step 1: drop beads
    for (i, &element_value) in arr.iter().enumerate() {
        for j in 0..(element_value as usize) {
            beads[i][j] = 1;
        }
    }

    // step 2: bread fall down
    for j in 0..max_val {
        let mut sum = 0;

        for i in 0..num_elements {
            sum += beads[i][j];
            beads[i][j] = 0;
        }

        for i in (num_elements - sum)..num_elements {
            beads[i][j] = 1;
        }
    }

    // step 3: read sorted value
    for i in 0..num_elements {
        let mut count = 0;

        for j in 0..max_val {
            count += beads[i][j]
        }

        arr[i] = count as i32;
    }

    return Ok(arr);
}
