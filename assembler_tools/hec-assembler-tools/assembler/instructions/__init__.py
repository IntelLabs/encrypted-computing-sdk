
def tokenizeFromLine(line: str) -> list:
        """
        Tokenizes a line of text and extracts any comment present.

        This function processes a line of text, removing line breaks and splitting the line
        into tokens based on commas. It also identifies and extracts comments, which are
        denoted by the pound symbol `#`.

        Args:
            line (str): Line of text to tokenize.

        Returns:
            tuple: A tuple containing the tokens and the comment. The `tokens` are a tuple of strings,
            and `comment` is a string. The `comment` is an empty string if no comment is found in the line.
        """
        tokens = tuple()
        comment = ""
        if line:
            line = ''.join(line.splitlines()) # remove line breaks
            comment_idx = line.find('#')
            if comment_idx >= 0:
                # Found a comment
                comment = line[comment_idx + 1:]
                line = line[:comment_idx]
            tokens = tuple(map(lambda s: s.strip(), line.split(',')))
        retval = (tokens, comment)
        return retval
