use std::path::Path;

/** Never turn one selected filesystem name into another by replacing invalid bytes. */
pub(crate) fn unicode_path(path: &Path) -> Result<&str, &'static str> {
    path.to_str()
        .ok_or("The selected path cannot be represented as a Java Unicode string")
}

#[cfg(test)]
mod tests {
    use super::unicode_path;
    use std::path::Path;

    #[test]
    fn normal_unicode_names_are_preserved() {
        assert_eq!(
            unicode_path(Path::new("Résumé/你好 😀.txt")).unwrap(),
            "Résumé/你好 😀.txt"
        );
    }

    #[cfg(unix)]
    #[test]
    fn invalid_utf8_does_not_alias_a_replacement_character_filename() {
        use std::ffi::OsString;
        use std::os::unix::ffi::OsStringExt;
        use std::path::PathBuf;
        let raw = PathBuf::from(OsString::from_vec(vec![b'a', 0xff]));
        assert!(unicode_path(&raw).is_err());
        assert_eq!(unicode_path(Path::new("a\u{fffd}")).unwrap(), "a\u{fffd}");
    }
}
