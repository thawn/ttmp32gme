package TTMp32Gme::DbUpdate;

use strict;
use warnings;

my $updates = {
	'0.1.0' => <<'END',
UPDATE "config" SET value='0.1.0' WHERE param='version';
END
	'0.2.0' => <<'END',
UPDATE "config" SET value='0.2.0' WHERE param='version';
END
	'0.2.1' => <<'END',
UPDATE "config" SET value='0.2.1' WHERE param='version';
END
};

sub update {
	my ( $dbVersion, $dbh ) = @_;

	foreach my $u ( sort keys %{$updates} ) {
		if ( Perl::Version->new($u)->numify > $dbVersion->numify ) {
			my $batch = DBIx::MultiStatementDo->new( dbh => $dbh );
			$batch->do( $updates->{$u} )
				or die "Can't update config file.\n\tError: "
				. $batch->dbh->errstr . "\n";
		}
	}

	return 1;
}

1;
