#!/usr/bin/env perl

use strict;
use warnings;

use Path::Class;
use Getopt::Long;
use Perl::Version;
use DBI;
use DBIx::MultiStatementDo;

my $version_str = "0.3.3";

# Command line startup options
#  Usage: update_version [-v|--version]
GetOptions( "version=s" => \$version_str );    # Get the version number
my $version = Perl::Version->new($version_str);

print STDOUT "Updating files to version $version:\n";

sub replace_version {
	my ( $path, $regex ) = @_;
	my $file = file($path);
	print STDOUT "  Updating " . $file->basename . "\n";
	my $data = $file->slurp();
	$data =~ s/$regex/$1$version$2/g;

	#print $data;
	$file->spew($data);
}
my %file_list = (
	'ttmp32gme.pl' => '(Perl::Version->new\(")[\d\.]*("\))',
	file( '..', 'build', 'mac', 'ttmp32gme.app', 'Contents', 'Info.plist' )->stringify() =>
		'(ttmp32gme |<string>)\d\.\d\.\d(</string>)',
);

for my $path ( keys %file_list ) {
	replace_version( $path, $file_list{$path} );
}

my $dbh = DBI->connect( "dbi:SQLite:dbname=config.sqlite", "", "" )
	or die "Could not open config file.\n";
my $config    = $dbh->selectrow_hashref(q( SELECT value FROM config WHERE param LIKE "version" ));
my $dbVersion = Perl::Version->new( $config->{'value'} );
if ( $version->numify > $dbVersion->numify ) {
	print STDOUT "Updating config...\n";

	require TTMp32Gme::DbUpdate;
	TTMp32Gme::DbUpdate::update( $dbVersion, $dbh );

	print STDOUT "Update successful.\n";
}
print STDOUT "Update done.\n";
