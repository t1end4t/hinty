use rust_template::sorts::bead_sort;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bead_sort() {
        let arr = vec![6, 11, 12, 4, 1, 5];
        let result = bead_sort(arr).unwrap();

        assert_eq!(result, vec![1, 4, 5, 6, 11, 12]);
    }
}
