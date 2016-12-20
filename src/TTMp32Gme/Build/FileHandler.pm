
package TTMp32Gme::Build::FileHandler;

use strict;
use warnings;

use PAR;
use File::Path qw(make_path remove_tree);
use Path::Class;
use File::Copy qw(move);
use File::Basename qw(dirname basename);

require Exporter;
our @ISA = qw(Exporter);
our @EXPORT =
	qw(getLibraryPath loadTemplates loadAssets checkConfigFile openBrowser loadStatic makeTempAlbumDir makeNewAlbumDir moveToAlbum removeTempDir);

my @build_imports =
	qw(loadFile getLibraryPath loadTemplates loadAssets checkConfigFile openBrowser);
if ( PAR::read_file('build.txt') ) {
	if ( $^O eq 'darwin' ) {
		require TTMp32Gme::Build::Mac;
		import TTMp32Gme::Build::Mac @build_imports;
	} elsif ( $^O =~ /MSWin/ ) {
		require TTMp32Gme::Build::Win;
		import TTMp32Gme::Build::Win @build_imports;
	}
} else {
	require TTMp32Gme::Build::Perl;
	import TTMp32Gme::Build::Perl @build_imports;
}

sub loadStatic {
	my $static = {};
	my @staticFiles =
		( 'upload.html', 'library.html', 'print.html', 'help.html', );
	foreach my $file (@staticFiles) {
		$static->{$file} = loadFile($file);
	}

	return $static;
}

sub makeTempAlbumDir {
	my $albumTitle = $_[0];
	my $albumPath = ( dir( getLibraryPath(), 'temp', $albumTitle ) )->stringify;
	make_path($albumPath);
	return $albumPath;
}

sub makeNewAlbumDir {
	my $albumTitle = $_[0];
	my $albumPath  = ( dir( getLibraryPath(), $albumTitle ) )->stringify;
	my $count      = 0;
	while ( -d $albumPath ) {
		$albumPath =~ s/_\d*$//;
		$albumPath .= '_' . $count;
		$count++;
	}
	make_path($albumPath);
	return $albumPath;

}

sub moveToAlbum {
	my ( $albumPath, $filePath ) = @_;
	my $fileName = basename($filePath);
	my $newPath = ( file( $albumPath, $fileName ) )->stringify;
	move( $filePath, $newPath );
	return $fileName;
}

sub removeTempDir {
	my $tempPath = ( dir( getLibraryPath(), 'temp' ) )->stringify;
	if ( $tempPath =~ /temp/ && -d $tempPath ) {
			print "deleting $tempPath";
			remove_tree($tempPath);
	}
}

1;
