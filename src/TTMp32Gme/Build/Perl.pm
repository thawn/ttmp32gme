
package TTMp32Gme::Build::Perl;

use strict;
use warnings;

use File::Find;
require Exporter;
our @ISA    = qw(Exporter);
our @EXPORT = qw(loadFile getLibraryPath loadTemplates loadAssets checkConfigFile openBrowser get_executable_path);

sub loadFile {
 	my $path = $_[0];
 	my $file;
 	open( $file, '<', $path) or die "Can't open '$path': $!";
 	my $content = join( "", <$file> );
 	close($file);
 	return $content;
}

sub getLibraryPath {
	return 'library';
}

sub loadTemplates {
	my %templates = ();
	$templates{'base'} =
	  Text::Template->new( TYPE => 'FILE', SOURCE => 'base.html' );
	$templates{'config'} =
	  Text::Template->new( TYPE => 'FILE', SOURCE => 'config.html' );

	return %templates;
}

sub loadAssets {
	my %assets = ();
	find(sub {
		my $content = loadFile($_) if -f;
		my $mime;
		if ( $_ =~ /.js$/ ) {
			$mime = 'text/javascript';
		} elsif ( $_ =~ /.css$/ ) {
			$mime = 'text/css';
		} else {
			$mime = '';
		}
		$assets{"/".$File::Find::name} = sub {
		my ($httpd, $req) = @_;

		$req->respond({ content => [$mime, $content] });
		}
	}, 'assets/');
	
	
	return %assets;
}

sub checkConfigFile {
	if ( -f 'config.sqlite' ) {
		return 'config.sqlite';
	}
	else {
		return 0;
	}
}

sub openBrowser {

	#Do nothing
	return 1;
}

sub get_executable_path {
	my $exe_name = $_[0];
	return '../../../lib/'. $exe_name;
}

1;
