package TTMp32Gme::TttoolHandler;

use strict;
use warnings;

use Path::Class;
use Cwd;

use Data::Dumper;

use Log::Message::Simple qw(msg error);

use TTMp32Gme::Build::FileHandler;
use TTMp32Gme::LibraryHandler;

require Exporter;
our @ISA    = qw(Exporter);
our @EXPORT = qw(make_gme generate_oid_images);

## internal functions:

sub generate_codes_yaml {
	my ( $yaml_file, $dbh ) = @_;
	my $fh = $yaml_file->openr();

	#first seek to the scripts section
	while ( my $row = <$fh> ) {
		if ( $row =~ /scripts:/ ) {
			last;
		}
	}
	my @scripts;
	while ( my $row = <$fh> ) {
		$row =~ s/\s*(.*)\R/$1/g;
		if ( $row =~ /:$/ ) {
			$row =~ s/://;
			push( @scripts, $row );
		}
	}
	close($fh);
	my $query        = "SELECT * FROM script_codes";
	my $codes        = $dbh->selectall_hashref( $query, 'script' );
	
	my @sorted_codes;
	foreach my $script (keys %{$codes}) {
		push(@sorted_codes, $codes->{$script}{'code'});
	}
	
	@sorted_codes = sort { $b <=> $a } @sorted_codes ;
	my $last_code    = $sorted_codes[0];

	my $filename = $yaml_file->basename();
	$filename =~ s/yaml$/codes.yaml/;
	my $codes_file = file( $yaml_file->dir(), $filename );
	$fh = $codes_file->openw();
	print $fh '# This file contains a mapping from script names to oid codes.
# This way the existing scripts are always assigned to the the
# same codes, even if you add further scripts.
# 
# You can copy the contents of this file into the main .yaml file,
# if you want to have both together.
# 
# If you delete this file, the next run of "ttool assemble" might
# use different codes for your scripts, and you might have to re-
# create the images for your product.
scriptcodes:
';
	foreach my $script (@scripts) {
		if ( $codes->{$script}{'code'} ) {
			print $fh "  $script: $codes->{$script}{'code'}\n";
		} else {
			$last_code++;
			if ( $last_code > 14999 ) {
				my %code_test = map { $_ => 1 } @sorted_codes;
				$last_code = 1000;
				while ( $code_test{$last_code} ) {
					$last_code++;
				}
				if ( $last_code > 14999 ) {
					die("Cannot create script. All script codes are used up.");
				}
				my $qh = $dbh->prepare(q(INSERT INTO script_codes VALUES (?,?) ));
				$qh->execute( ( $script, $last_code ) );
				unshift( @sorted_codes, $last_code );
				$codes->{$script}{'code'} = $last_code;
			}
			print $fh "  $script: $last_code\n";
		}
	}
	close($fh);
	return $codes_file;
}

sub convert_tracks {
	my ( $album, $yaml_file, $config ) = @_;
	my $media_path = dir( $album->{'path'}, "audio" );
	my @tracks = grep { $_ =~ /^track_/ } keys %{$album};
	$media_path->mkpath();
	if ( $config->{'tt_audio_format'} eq 'ogg' ) {

		#todo: convert mp3s to ogg if desired
	} else {
		foreach my $i ( 0 .. $#tracks ) {
			file( $album->{'path'}, $album->{ $tracks[$i] }->{'filename'} )
				->copy_to( file( $media_path, "track_$i.mp3" ) );
		}
	}
	my $next = "  next:\n";
	my $prev = "  prev:\n";
	my $track_scripts;
	foreach my $i ( 0 .. $#tracks ) {
		if ( $i < $#tracks ) {
			if ( $i < $#tracks - 1 ) {
				$next .=
"  - \$current==$i? \$current:=@{[$i+1]} P(@{[$i+1]}) J(t@{[$i+2]})\n";
			} else {
				$next .= "  - \$current==$i? \$current:=@{[$i+1]} P(@{[$i+1]}) C\n";
			}
		}
		if ( $i > 0 ) {
			$prev .=
				"  - \$current==$i? \$current:=@{[$i-1]} P(@{[$i-1]}) J(t@{[$i]})\n";
		}
		if ( $i < $#tracks ) {
			$track_scripts .= "  t$i:\n  - \$current:=$i P($i) J(t@{[$i+1]})\n";
		} else {
			$track_scripts .= "  t$i:\n  - \$current:=$i P($i) C\n";
		}
	}

	# add track code to the yaml file:
	my $fh = $yaml_file->opena();

	#todo: test, if windows systems need a different path separator in yaml file
	print $fh "media-path: audio/track_%s\n";
	print $fh "init: \$current:=0\n";
	print $fh "welcome: " . join( ', ', ( 0 .. $#tracks ) ) . "\n";
	print $fh "scripts:\n";
	print $fh $next;
	print $fh $prev;
	print $fh "  stop:\n  - C C\n";
	print $fh $track_scripts;
	close($fh);
	return $media_path;
}

sub get_tttool_command {
	my ($dbh)      = @_;
	my $tt_command = get_executable_path('tttool');
	my $tt_params  = $dbh->selectall_hashref(
q(SELECT * FROM config WHERE param LIKE 'tt\_%' ESCAPE '\' AND value IS NOT NULL),
		'param'
	);
	foreach my $param ( keys %{$tt_params} ) {
		$tt_command .= " -$param $tt_params->{$param}";
	}
	return $tt_command;
}

##exported functions

sub make_gme {
	my ( $oid, $config, $dbh ) = @_;
	my $album = get_album( $oid, $dbh );
	$album->{'old_oid'} = $oid;
	my $yaml_file = file( $album->{'path'},
		sprintf( '%s.yaml', cleanup_filename( $album->{'album_title'} ) ) );
	my $fh = $yaml_file->openw();
	print $fh "#this file was generated automatically by ttmp32gme\n";
	print $fh "product-id: $oid\n";
	close($fh);
	my $media_path = convert_tracks( $album, $yaml_file, $config );
	my $codes_file = generate_codes_yaml( $yaml_file, $dbh );
	my $maindir = cwd();
	chdir( $album->{'path'} ) or die "Can't open '$album->{'path'}': $!";
	my $tt_command  = get_tttool_command($dbh);

	#todo: detect errors in the output of tttool
	my $yaml      = $yaml_file->basename();
	my $tt_output = `$tt_command assemble $yaml`;
	msg( $tt_output, 1 );
	$tt_output = `$tt_command oid-codes $yaml`;
	msg( $tt_output, 1 );
	chdir($maindir);
	my $gme_filename = $yaml_file->basename();
	$gme_filename =~ s/yaml$/gme/;
	$album->{'gme_file'} = $gme_filename;
	my @selector = ($oid);
	updateAlbum( $album, $dbh );
	remove_library_dir($media_path);
	return $oid;
}

1;