use hinty::sorts::bead_sort;

fn main() {
    let arr = vec![6, 11, 12, 4, 1, 5];
    let result = bead_sort(arr);

    // print out result
    println!("Sorted array: {:?}", result);
}
