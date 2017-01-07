package TTMp32Gme::Build::FileHandler;

use strict;
use warnings;

use PAR;
use Path::Class;

require Exporter;
our @ISA = qw(Exporter);
our @EXPORT =
	qw(loadTemplates loadAssets openBrowser getLibraryPath checkConfigFile loadStatic makeTempAlbumDir makeNewAlbumDir moveToAlbum removeTempDir clearAlbum removeAlbum cleanup_filename remove_library_dir get_executable_path get_oid_cache get_tiptoi_dir);

my @build_imports =
	qw(loadFile get_local_storage get_par_tmp loadTemplates loadAssets openBrowser);

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

sub getLibraryPath {
	my $library = dir( get_local_storage(), 'library' );
	$library->mkpath();
	return $library->stringify();
}

sub checkConfigFile {
	my $configdir = get_local_storage();
	my $configfile = file( $configdir, 'config.sqlite' );
	if ( !-f $configfile ) {
		my $cfgToCopy = file( get_par_tmp(), 'config.sqlite' );
		$cfgToCopy->copy_to($configfile)
			or die "Could not create local copy of config file '$cfgToCopy': $!";
	}
	return $configfile;
}

sub loadStatic {
	my $static = {};
	my @staticFiles = ( 'upload.html', 'library.html', 'help.html', );
	foreach my $file (@staticFiles) {
		$static->{$file} = loadFile($file);
	}

	return $static;
}

sub makeTempAlbumDir {
	my $albumPath = dir( getLibraryPath(), 'temp', $_[0] );
	$albumPath->mkpath();
	return $albumPath;
}

sub makeNewAlbumDir {
	my $albumTitle = $_[0];

	#make sure no album hogs the temp directory
	if ( $albumTitle eq 'temp' ) {
		$albumTitle .= '_0';
	}
	my $albumPath = ( dir( getLibraryPath(), $albumTitle ) )->stringify;
	my $count = 0;
	while ( -d $albumPath ) {
		$albumPath =~ s/_\d*$//;
		$albumPath .= '_' . $count;
		$count++;
	}
	$albumPath = dir($albumPath);
	$albumPath->mkpath();
	return $albumPath->stringify;
}

sub moveToAlbum {
	my ( $albumPath, $filePath ) = @_;
	my $file = file($filePath);
	my $album_file = $file->move_to( file( $albumPath, $file->basename() ) );
	return $album_file->basename();
}

sub removeTempDir {
	my $tempPath = dir( getLibraryPath(), 'temp' );
	if ( $tempPath =~ /temp/ && -d $tempPath ) {
		print "deleting $tempPath\n";
		$tempPath->rmtree();
	}
	return 1;
}

sub clearAlbum {
	my ( $path, $file_list ) = @_;
	my $libraryPath = getLibraryPath();
	if ( $path =~ /^$libraryPath/ ) {
		foreach my $file ( @{$file_list} ) {
			if ($file) {
				my $full_file = file( $path, $file );
				if ( -f $full_file ) {
					$full_file->remove();
				}
			}
		}
		return 1;
	} else {
		return 0;
	}
}

sub removeAlbum {
	my ($path) = @_;
	my $libraryPath = getLibraryPath();
	if ( $path =~ /^$libraryPath/ ) {
		( dir($path) )->rmtree();
		return 1;
	} else {
		return 0;
	}
}

sub cleanup_filename {
	my $filename = $_[0];
	$filename =~ s/\s/_/g;
	$filename =~ s/[^A-Za-z0-9_\-\.]//g;
	$filename =~ s/\.\./\./g;
	$filename =~ s/\.$//g;
	return $filename;
}

sub remove_library_dir {
	my ($media_path) = @_;
	my $media_dir    = dir($media_path);
	my $libraryPath  = getLibraryPath();
	if ( $media_dir =~ /^$libraryPath/ ) {
		$media_dir->rmtree();
		return 1;
	} else {
		return 0;
	}
}

sub get_executable_path {
	my $exe_name = $_[0];
	return ( file( get_par_tmp(), 'lib', $exe_name ) )->stringify();
}

sub get_oid_cache {
	my $oid_cache = dir( get_local_storage(), 'oid_cache' );
	if ( !-d $oid_cache ) {
		$oid_cache->mkpath();
		my $cache = dir( get_par_tmp(), 'oid_cache' );
		$cache->recurse(
			callback => sub {
				my ($file) = @_;
				if ( -f $file && $file =~ /\.png$/ ) {
					$file->copy_to( file( $oid_cache, $file->basename() ) );
				}
			}
		);
	}
	return $oid_cache->stringify();
}

sub get_tiptoi_dir {
	if ( $^O eq 'darwin' ) {
		my $tiptoi_path = dir( '', 'Volumes', 'tiptoi' );
		if ( -w $tiptoi_path ) {
			return $tiptoi_path;
		}
	}
	return 0;
}

1;
