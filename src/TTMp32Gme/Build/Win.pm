package TTMp32Gme::Build::Win;

use strict;
use warnings;

use Path::Class;

require Exporter;
our @ISA    = qw(Exporter);
our @EXPORT = qw(loadFile get_local_storage get_par_tmp loadTemplates loadAssets openBrowser);

sub loadFile {
	my $path    = $_[0];
	my $content = PAR::read_file($path);
	return $content;
}

sub get_local_storage {
	my $storage = dir( $ENV{'APPDATA'}, 'ttmp32gme' );
	$storage->mkpath();
	return $storage;
}

sub get_par_tmp {
	return dir( $ENV{'PAR_TEMP'}, 'inc' );
}

sub loadTemplates {
	my %templates = ();
	my $manifest  = PAR::read_file('templates.list');
	open my $fh, '<', \$manifest;
	while ( my $path = <$fh> ) {
		$path =~ s/\R//g;
		my ($name) = $path =~ /.*\/(.*)\.html$/;
		$templates{$name} =
			Text::Template->new( TYPE => 'STRING', SOURCE => loadFile($path) );
	}
	return %templates;
}

sub loadAssets {
	my %assets   = ();
	my $manifest = PAR::read_file('assets.list');
	open my $fh, '<', \$manifest;
	while ( my $path = <$fh> ) {
		$path =~ s/\R//g;
		my $content = loadFile($path);
		my $mime;
		if ( $path =~ /.js$/ ) {
			$mime = 'text/javascript';
		} elsif ( $path =~ /.css$/ ) {
			$mime = 'text/css';
		} else {
			$mime = '';
		}
		$assets{ "/" . $path } = sub {
			my ( $httpd, $req ) = @_;

			$req->respond( { content => [ $mime, $content ] } );
		}
	}

	return %assets;
}

sub openBrowser {
	my %config = @_;
	`start http://127.0.0.1:$config{'port'}/`;
	return 1;
}

1;
