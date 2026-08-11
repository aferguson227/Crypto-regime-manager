# V69 Release/Runtime Validation Separation

Software release identity and mutable runtime publication snapshots are now validated separately. Release-owned metadata remains strict. Older runtime snapshots report refresh-required without invalidating the source release; future-version snapshots remain fatal.
